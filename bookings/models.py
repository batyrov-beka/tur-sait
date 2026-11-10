from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from tours.models import Hotel, Tour

CHILD_PRICE_RATE = Decimal("0.5")  # бала үчүн тур баасынын 50%


class PromoCode(models.Model):
    code = models.CharField("Код", max_length=30, unique=True, help_text="Мисалы: SUMMER10 (баш тамгалар менен)")
    discount_percent = models.PositiveSmallIntegerField(
        "Арзандатуу, %", validators=[MinValueValidator(1), MaxValueValidator(90)])
    valid_until = models.DateField("Качанга чейин", null=True, blank=True)
    max_uses = models.PositiveIntegerField("Колдонуу лимити", null=True, blank=True, help_text="Бош = чексиз")
    used_count = models.PositiveIntegerField("Колдонулду", default=0)
    is_active = models.BooleanField("Активдүү", default=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоддор"

    def __str__(self):
        return f"{self.code} (−{self.discount_percent}%)"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.valid_until and self.valid_until < timezone.localdate():
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True

    @classmethod
    def find_valid(cls, code):
        code = (code or "").strip().upper()
        if not code:
            return None
        promo = cls.objects.filter(code=code).first()
        return promo if promo and promo.is_valid else None


class Booking(models.Model):
    STATUS_NEW = "new"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_NEW, _("Жаңы")),
        (STATUS_CONFIRMED, _("Ырасталды")),
        (STATUS_PAID, _("Төлөндү")),
        (STATUS_CANCELLED, _("Жокко чыгарылды")),
        (STATUS_COMPLETED, _("Аяктады")),
    ]
    CANCELLABLE = (STATUS_NEW, STATUS_CONFIRMED)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings",
                             verbose_name="Колдонуучу")
    tour = models.ForeignKey(Tour, on_delete=models.PROTECT, related_name="bookings", verbose_name="Тур")
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings",
                              verbose_name="Мейманкана")
    travel_date = models.DateField("Учуу күнү")
    adults = models.PositiveSmallIntegerField("Чоңдор", default=1)
    children = models.PositiveSmallIntegerField("Балдар", default=0)
    full_name = models.CharField("Аты-жөнү", max_length=150)
    phone = models.CharField("Телефон", max_length=30)
    email = models.EmailField("Email", blank=True)
    comment = models.TextField("Комментарий", blank=True, max_length=1000)
    promo = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings",
                              verbose_name="Промокод")
    discount = models.DecimalField("Арзандатуу (сом)", max_digits=12, decimal_places=0, default=0)
    total_price = models.DecimalField("Жалпы баасы (сом)", max_digits=12, decimal_places=0, default=0)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    admin_note = models.TextField("Менеджердин белгиси", blank=True)
    created_at = models.DateTimeField("Түзүлгөн", auto_now_add=True)
    updated_at = models.DateTimeField("Өзгөртүлгөн", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Брондоо"
        verbose_name_plural = "Брондоолор"

    def __str__(self):
        return f"#{self.pk} {self.full_name} — {self.tour}"

    @staticmethod
    def calculate_price(tour, adults, children, hotel=None, promo=None):
        """
        Баа: чоңдор × тур + балдар × тур × 50% + мейманкана × түн саны, андан промокод арзандатуусу.
        Кайтарат: (жалпы баа, арзандатуу).
        """
        total = tour.price * adults + tour.price * CHILD_PRICE_RATE * children
        if hotel:
            total += hotel.price_per_night * tour.duration_days
        discount = Decimal("0")
        if promo:
            discount = (total * promo.discount_percent / Decimal("100")).quantize(Decimal("1"))
        return (total - discount).quantize(Decimal("1")), discount

    def save(self, *args, **kwargs):
        self.total_price, self.discount = self.calculate_price(
            self.tour, self.adults, self.children, self.hotel, self.promo)
        super().save(*args, **kwargs)

    @property
    def people(self):
        return self.adults + self.children

    @property
    def can_cancel(self):
        return self.status in self.CANCELLABLE

    @property
    def status_css(self):
        return {
            self.STATUS_NEW: "info",
            self.STATUS_CONFIRMED: "success",
            self.STATUS_PAID: "success",
            self.STATUS_CANCELLED: "danger",
            self.STATUS_COMPLETED: "muted",
        }.get(self.status, "info")
