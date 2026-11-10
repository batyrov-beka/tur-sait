"""
Менеджерге билдирүү жөнөтүү: Telegram (жөндөлсө) + email.
Telegram үчүн чөйрө өзгөрмөлөрү: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
(бот @BotFather аркылуу түзүлөт; chat id'ни @userinfobot көрсөтөт).
Ката болсо сайт токтобойт — ката логго гана жазылат.
"""
import json
import logging
import threading
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send_telegram(text):
    token, chat_id = settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return
    data = json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data, headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception:  # noqa: BLE001
        logger.exception("Telegram notification failed")


def notify_manager(subject, text):
    """Фондо (thread) жөнөтөт — колдонуучу күтүп калбайт."""
    threading.Thread(target=_send_telegram, args=(f"🔔 {subject}\n\n{text}",), daemon=True).start()
    try:
        send_mail(f"IT Travel: {subject}", text, None, [settings.BOOKING_NOTIFY_EMAIL], fail_silently=False)
    except Exception:  # noqa: BLE001
        logger.exception("Email notification failed")
