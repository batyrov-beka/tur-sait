"""Админканын башкы бетиндеги статистика панели."""
from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone

from bookings.models import Booking
from tours.models import ContactMessage, Review, Subscriber, Tour

register = template.Library()


@register.inclusion_tag("admin/dashboard.html")
def admin_dashboard():
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    bookings = Booking.objects.all()
    revenue = (bookings.filter(status__in=[Booking.STATUS_PAID, Booking.STATUS_COMPLETED])
               .aggregate(total=Sum("total_price"))["total"] or 0)
    pipeline = (bookings.filter(status__in=[Booking.STATUS_NEW, Booking.STATUS_CONFIRMED])
                .aggregate(total=Sum("total_price"))["total"] or 0)
    status_counts = []
    total = bookings.count() or 1
    for code, label in Booking.STATUS_CHOICES:
        count = bookings.filter(status=code).count()
        status_counts.append({"code": code, "label": label, "count": count, "pct": round(count * 100 / total)})
    return {
        "cards": [
            {"icon": "🆕", "label": "Жаңы арыздар", "value": bookings.filter(status=Booking.STATUS_NEW).count(),
             "url": "/admin/bookings/booking/?status__exact=new", "accent": "orange"},
            {"icon": "📅", "label": "Ушул айда брондоо", "value": bookings.filter(created_at__gte=month_start).count(),
             "url": "/admin/bookings/booking/", "accent": "teal"},
            {"icon": "💰", "label": "Төлөнгөн (сом)", "value": revenue, "money": True,
             "url": "/admin/bookings/booking/?status__exact=paid", "accent": "green"},
            {"icon": "⏳", "label": "Күтүүдө (сом)", "value": pipeline, "money": True,
             "url": "/admin/bookings/booking/?status__exact=confirmed", "accent": "blue"},
            {"icon": "👤", "label": "Колдонуучулар", "value": get_user_model().objects.count(),
             "sub": f"+{get_user_model().objects.filter(date_joined__gte=week_ago).count()} жумада",
             "url": "/admin/auth/user/", "accent": "purple"},
            {"icon": "✉️", "label": "Жооп күткөн билдирүүлөр",
             "value": ContactMessage.objects.filter(is_processed=False).count(),
             "url": "/admin/tours/contactmessage/?is_processed__exact=0", "accent": "orange"},
            {"icon": "⭐", "label": "Пикирлер", "value": Review.objects.count(),
             "url": "/admin/tours/review/", "accent": "yellow"},
            {"icon": "🧳", "label": "Активдүү турлар", "value": Tour.objects.filter(is_active=True).count(),
             "sub": f"{Subscriber.objects.count()} жазылуучу", "url": "/admin/tours/tour/", "accent": "teal"},
        ],
        "status_counts": status_counts,
        "latest": bookings.select_related("tour")[:6],
    }
