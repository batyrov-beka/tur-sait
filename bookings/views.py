import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from tours.models import Tour
from tours.notify import notify_manager

from .forms import BookingForm
from .models import Booking, PromoCode

logger = logging.getLogger(__name__)


def _notify_manager(request, booking):
    """Менеджерге жаңы брондоо жөнүндө кат. Ката болсо сайт токтобойт."""
    admin_url = request.build_absolute_uri(reverse("admin:bookings_booking_change", args=[booking.pk]))
    body = (
        f"Жаңы брондоо #{booking.pk}\n"
        f"Тур: {booking.tour.title_ky}\n"
        f"Күнү: {booking.travel_date:%d.%m.%Y}\n"
        f"Кишилер: {booking.adults} чоң, {booking.children} бала\n"
        f"Мейманкана: {booking.hotel or '—'}\n"
        f"Кардар: {booking.full_name}, {booking.phone}, {booking.email or '—'}\n"
        f"Промокод: {booking.promo.code if booking.promo else '—'} (−{booking.discount} сом)\n"
        f"Баасы: {booking.total_price} сом\n"
        f"Комментарий: {booking.comment or '—'}\n\n"
        f"Админкада ачуу: {admin_url}"
    )
    notify_manager(f"Жаңы брондоо #{booking.pk}", body)


@login_required
def booking_create(request, slug):
    tour = get_object_or_404(Tour.objects.active().select_related("country"), slug=slug)
    if request.method == "POST":
        form = BookingForm(request.POST, tour=tour)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.tour = tour
            booking.promo = form.cleaned_data.get("promo_code")
            booking.save()
            if booking.promo:
                PromoCode.objects.filter(pk=booking.promo.pk).update(used_count=F("used_count") + 1)
            _notify_manager(request, booking)
            messages.success(request, _("Рахмат! Арызыңыз кабыл алынды. Менеджер жакында байланышат."))
            return redirect("bookings:detail", pk=booking.pk)
    else:
        user = request.user
        form = BookingForm(
            tour=tour,
            initial={
                "full_name": user.get_full_name() or user.username,
                "email": user.email,
                "hotel": request.GET.get("hotel") or None,
            },
        )
    return render(request, "bookings/booking_form.html", {"form": form, "tour": tour})


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("tour__country", "hotel"), pk=pk, user=request.user)
    return render(request, "bookings/booking_detail.html", {"booking": booking})


@login_required
@require_POST
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.can_cancel:
        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        messages.info(request, _("Брондоо жокко чыгарылды."))
    else:
        messages.error(request, _("Бул брондоону жокко чыгарууга болбойт."))
    return redirect("accounts:cabinet")


def price_preview(request, slug):
    """JS үчүн: тандалган параметрлер боюнча бааны эсептеп берет (JSON)."""
    from django.http import JsonResponse

    tour = get_object_or_404(Tour.objects.active(), slug=slug)
    try:
        adults = max(1, min(int(request.GET.get("adults", 1)), tour.max_people))
        children = max(0, min(int(request.GET.get("children", 0)), tour.max_people))
    except ValueError:
        adults, children = 1, 0
    hotel_id = request.GET.get("hotel", "")
    hotel = tour.country.hotels.filter(pk=hotel_id, is_active=True).first() if hotel_id.isdigit() else None
    promo = PromoCode.find_valid(request.GET.get("promo_code"))
    total, discount = Booking.calculate_price(tour, adults, children, hotel, promo)
    return JsonResponse({
        "total": int(total),
        "discount": int(discount),
        "promo_ok": promo is not None,
        "promo_percent": promo.discount_percent if promo else 0,
    })


# ---------------------------------------------------------------------------
# Онлайн төлөм
# ---------------------------------------------------------------------------
from django.http import HttpResponse, HttpResponseBadRequest  # noqa: E402
from django.views.decorators.csrf import csrf_exempt  # noqa: E402

from .models import Payment  # noqa: E402
from .payments import PaymentError, get_provider  # noqa: E402


def _notify_paid(payment):
    b = payment.booking
    notify_manager(
        f"Төлөм келди: брондоо #{b.pk}",
        f"{b.full_name}, {b.phone}\nТур: {b.tour.title_ky}\nСумма: {payment.amount} сом\n"
        f"Провайдер: {payment.provider} {payment.external_id}",
    )


@login_required
@require_POST
def pay_start(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("tour"), pk=pk, user=request.user)
    if not booking.can_pay:
        messages.error(request, _("Бул брондоону азыр төлөөгө болбойт."))
        return redirect("bookings:detail", pk=pk)
    try:
        provider = get_provider()
        payment = Payment.objects.create(booking=booking, provider=provider.code, amount=booking.total_price)
        url = provider.start(request, payment)
    except PaymentError as exc:
        messages.error(request, _("Төлөмдү баштоо мүмкүн болгон жок: %(err)s") % {"err": exc})
        return redirect("bookings:detail", pk=pk)
    return redirect(url)


@login_required
def test_checkout(request, payment_id):
    """Тест режиминин төлөм барагы: чыныгы карта сурабайт, жыйынтыкты баскыч менен тандайсыз."""
    payment = get_object_or_404(Payment.objects.select_related("booking__tour"), pk=payment_id,
                                booking__user=request.user, provider="test")
    if request.method == "POST" and payment.status == Payment.STATUS_PENDING:
        if request.POST.get("result") == "success":
            if payment.mark_paid({"test": True}):
                _notify_paid(payment)
            messages.success(request, _("Төлөм ийгиликтүү өттү! Рахмат."))
        else:
            payment.mark_failed({"test": True})
            messages.error(request, _("Төлөм ийгиликсиз болду. Кайра аракет кылып көрүңүз."))
        return redirect("bookings:detail", pk=payment.booking_id)
    return render(request, "bookings/test_checkout.html", {"payment": payment})


@login_required
def payment_return(request, payment_id):
    """Freedom Pay'ден кайтып келгенде. Акыркы статусту result_url (сервер-сервер) аныктайт."""
    payment = get_object_or_404(Payment, pk=payment_id, booking__user=request.user)
    if payment.status == Payment.STATUS_PAID:
        messages.success(request, _("Төлөм ийгиликтүү өттү! Рахмат."))
    elif payment.status == Payment.STATUS_FAILED:
        messages.error(request, _("Төлөм ийгиликсиз болду. Кайра аракет кылып көрүңүз."))
    else:
        messages.info(request, _("Төлөм текшерилүүдө — бир нече секунддан кийин бетти жаңыртыңыз."))
    return redirect("bookings:detail", pk=payment.booking_id)


@csrf_exempt
@require_POST
def freedompay_result(request):
    """Freedom Pay'ден келген жыйынтык (pg_result_url)."""
    from .payments import FreedomPayProvider

    try:
        provider = FreedomPayProvider()
    except PaymentError:
        return HttpResponseBadRequest("not configured")
    params = request.POST.dict()
    if not provider.verify_callback(params):
        logger.warning("Freedom Pay: wrong signature %s", params.get("pg_order_id"))
        return HttpResponseBadRequest("bad signature")

    order_id = params.get("pg_order_id", "")
    try:
        payment_id = int(order_id.rsplit("-", 1)[-1])
        payment = Payment.objects.select_related("booking__tour").get(pk=payment_id)
    except (ValueError, Payment.DoesNotExist):
        xml = provider.callback_response("rejected", "Order not found")
        return HttpResponse(xml, content_type="application/xml")

    if params.get("pg_result") == "1":
        if str(payment.amount) != str(params.get("pg_amount", "")).split(".")[0]:
            logger.warning("Freedom Pay: amount mismatch for %s", order_id)
        payment.external_id = params.get("pg_payment_id", payment.external_id)
        payment.save(update_fields=["external_id"])
        if payment.mark_paid(params):
            _notify_paid(payment)
        xml = provider.callback_response("ok", "Order paid")
    else:
        payment.mark_failed(params)
        xml = provider.callback_response("ok", "Payment failed noted")
    return HttpResponse(xml, content_type="application/xml")
