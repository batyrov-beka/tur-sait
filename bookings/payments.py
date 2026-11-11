"""
Онлайн төлөм провайдерлери.

PAYMENT_PROVIDER=test        — тест режими: чыныгы акча алынбайт, төлөм ийгиликтүү/ийгиликсиз
                                баскыч менен симуляцияланат (демо жана диплом коргоо үчүн).
PAYMENT_PROVIDER=freedompay  — Freedom Pay Кыргызстан (карта, MBank, ELQR ж.б.).
                                Керек: FREEDOMPAY_MERCHANT_ID, FREEDOMPAY_SECRET_KEY.

Freedom Pay протоколу (https://freedompay.kg/docs-en/merchant-api/pay):
  1. Сервер init_payment.php'ге параметрлерди + pg_sig жиберет, жоопто pg_redirect_url келет.
  2. Кардар ошол баракта төлөйт.
  3. Freedom Pay pg_result_url'ге POST менен жыйынтыкты жиберет (pg_result=1 — ийгиликтүү),
     биз колтамганы текшерип, XML менен жооп беребиз.
"""
import hashlib
import logging
import secrets
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


# ---------------------------------------------------------------------------
# Freedom Pay колтамгасы (pg_sig)
# ---------------------------------------------------------------------------
def _flatten(params, prefix=""):
    """Колтамга үчүн: ички тизмелерди/сөздүктөрдү жалпак кылат (документтеги PHP мисалындай)."""
    flat = {}
    for key, value in params.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            for i, (k, v) in enumerate(value.items(), start=1):
                flat.update(_flatten({f"{name}{i:03d}": v}))
        else:
            flat[name] = "" if value is None else str(value)
    return flat


def make_signature(script_name, params, secret_key):
    """md5('скрипт;маанилер ачкыч боюнча иреттелген;secret_key')"""
    flat = _flatten({k: v for k, v in params.items() if k != "pg_sig"})
    values = [flat[k] for k in sorted(flat)]
    raw = ";".join([script_name, *values, secret_key])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def verify_signature(script_names, params, secret_key):
    received = (params.get("pg_sig") or "").lower()
    if not received:
        return False
    return any(secrets.compare_digest(make_signature(name, params, secret_key), received) for name in script_names)


# ---------------------------------------------------------------------------
# Провайдерлер
# ---------------------------------------------------------------------------
class TestProvider:
    code = "test"
    title = "Тест режими"
    is_test = True

    def start(self, request, payment):
        """Өзүбүздүн тест төлөм барагына жиберет."""
        return reverse("bookings:test_checkout", args=[payment.pk])


class FreedomPayProvider:
    code = "freedompay"
    title = "Freedom Pay"

    def __init__(self):
        self.merchant_id = settings.FREEDOMPAY_MERCHANT_ID
        self.secret_key = settings.FREEDOMPAY_SECRET_KEY
        self.api_url = settings.FREEDOMPAY_API_URL.rstrip("/")
        self.is_test = settings.FREEDOMPAY_TESTING_MODE
        if not self.merchant_id or not self.secret_key:
            raise PaymentError("FREEDOMPAY_MERCHANT_ID / FREEDOMPAY_SECRET_KEY коюлган эмес")

    def _abs(self, request, url):
        base = settings.SITE_URL.rstrip("/") if settings.SITE_URL else request.build_absolute_uri("/").rstrip("/")
        return base + url

    def start(self, request, payment):
        booking = payment.booking
        params = {
            "pg_merchant_id": self.merchant_id,
            "pg_order_id": payment.order_id,
            "pg_amount": str(payment.amount),
            "pg_currency": settings.FREEDOMPAY_CURRENCY,
            "pg_description": f"IT Travel: {booking.tour.title_ru} (#{booking.pk})"[:250],
            "pg_salt": secrets.token_hex(8),
            "pg_result_url": self._abs(request, reverse("bookings:freedompay_result")),
            "pg_success_url": self._abs(request, reverse("bookings:payment_return", args=[payment.pk])),
            "pg_failure_url": self._abs(request, reverse("bookings:payment_return", args=[payment.pk])),
            "pg_language": "ru",
        }
        if booking.email:
            params["pg_user_contact_email"] = booking.email
        digits = "".join(ch for ch in booking.phone if ch.isdigit())
        if digits:
            params["pg_user_phone"] = digits
        if self.is_test:
            params["pg_testing_mode"] = "1"
        params["pg_sig"] = make_signature("init_payment.php", params, self.secret_key)

        data = urllib.parse.urlencode(params).encode()
        try:
            with urllib.request.urlopen(f"{self.api_url}/init_payment.php", data=data, timeout=20) as resp:
                body = resp.read()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Freedom Pay init_payment failed")
            raise PaymentError("Төлөм системасына туташуу мүмкүн болгон жок") from exc

        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise PaymentError("Төлөм системасынан туура эмес жооп келди") from exc
        result = {child.tag: (child.text or "") for child in root}
        payment.payload = {"init": result}
        if result.get("pg_status") != "ok" or not result.get("pg_redirect_url"):
            payment.save(update_fields=["payload"])
            raise PaymentError(result.get("pg_error_description") or "Төлөмдү баштоо мүмкүн болгон жок")
        payment.external_id = result.get("pg_payment_id", "")
        payment.save(update_fields=["payload", "external_id"])
        return result["pg_redirect_url"]

    # --- result_url ---
    def result_script_names(self):
        # Колтамга result_url'дин акыркы бөлүгү (скрипттин аты) менен түзүлөт
        path = urllib.parse.urlparse(reverse("bookings:freedompay_result")).path
        last = [p for p in path.split("/") if p][-1]
        return [last, f"{last}/", path]

    def verify_callback(self, params):
        return verify_signature(self.result_script_names(), params, self.secret_key)

    def callback_response(self, status, description):
        params = {"pg_status": status, "pg_description": description, "pg_salt": secrets.token_hex(8)}
        params["pg_sig"] = make_signature(self.result_script_names()[0], params, self.secret_key)
        items = "".join(f"<{k}>{v}</{k}>" for k, v in params.items())
        return f'<?xml version="1.0" encoding="utf-8"?><response>{items}</response>'


def get_provider():
    if settings.PAYMENT_PROVIDER == "freedompay":
        return FreedomPayProvider()
    return TestProvider()
