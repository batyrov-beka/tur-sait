from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


def current_lang():
    """Учурдагы тилдин коду: 'ky' же 'ru'."""
    lang = (get_language() or "ky")[:2]
    return lang if lang in ("ky", "ru") else "ky"


PLACEHOLDERS = ["img/placeholder.svg", "img/placeholder-beach.svg", "img/placeholder-city.svg"]


def placeholder_url(variant=0):
    """Сүрөт жок болсо — өзүбүздүн SVG иллюстрация (тоо / пляж / шаар)."""
    from django.templatetags.static import static

    return static(PLACEHOLDERS[variant % len(PLACEHOLDERS)])


class TranslatedMixin:
    """Эки тилдүү талаалар: name_ky / name_ru -> obj.tr('name')."""

    def tr(self, field):
        value = getattr(self, f"{field}_{current_lang()}", "") or ""
        return value or getattr(self, f"{field}_ky", "") or ""


class ImageMixin:
    """Сүрөт: жүктөлгөн файл болсо ошону, болбосо шилтемени колдонобуз."""


    @property
    def cover_url(self):
        if getattr(self, "image", None):
            try:
                return self.image.url
            except ValueError:
                pass
        return getattr(self, "image_url", "") or placeholder_url(self.placeholder_variant)

    @property
    def placeholder_variant(self):
        tour_type = getattr(self, "tour_type", None)
        if tour_type:
            return {"beach": 1, "city": 2}.get(tour_type, 0)
        return self.pk or 0


class Country(TranslatedMixin, ImageMixin, models.Model):
    name_ky = models.CharField("Аталышы (кырг.)", max_length=100)
    name_ru = models.CharField("Аталышы (орус.)", max_length=100)
    slug = models.SlugField("URL аты", unique=True)
    short_ky = models.CharField("Кыскача (кырг.)", max_length=255, blank=True)
    short_ru = models.CharField("Кыскача (орус.)", max_length=255, blank=True)
    description_ky = models.TextField("Сүрөттөмө (кырг.)", blank=True)
    description_ru = models.TextField("Сүрөттөмө (орус.)", blank=True)
    image = models.ImageField("Сүрөт", upload_to="countries/", blank=True)
    image_url = models.URLField("Сүрөттүн шилтемеси", max_length=500, blank=True,
                                help_text="Файл жүктөлбөсө ушул шилтеме колдонулат")
    map_query = models.CharField("Картадагы жер", max_length=200, blank=True,
                                 help_text="Мисалы: Male, Maldives")
    # Пайдалуу маалымат
    visa_ky = models.CharField("Виза (кырг.)", max_length=200, blank=True, default="")
    visa_ru = models.CharField("Виза (орус.)", max_length=200, blank=True, default="")
    currency = models.CharField("Валюта", max_length=60, blank=True, default="", help_text="Мисалы: USD, EUR")
    flight_time = models.CharField("Учуу убактысы", max_length=60, blank=True, default="", help_text="Мисалы: 6–8 саат")
    best_season_ky = models.CharField("Мыкты мезгил (кырг.)", max_length=120, blank=True, default="")
    best_season_ru = models.CharField("Мыкты мезгил (орус.)", max_length=120, blank=True, default="")
    order = models.PositiveSmallIntegerField("Иреттик номер", default=0)
    is_active = models.BooleanField("Сайтта көрүнөт", default=True)

    class Meta:
        ordering = ["order", "name_ky"]
        verbose_name = "Өлкө"
        verbose_name_plural = "Өлкөлөр"

    def __str__(self):
        return self.name_ky

    @property
    def name(self):
        return self.tr("name")

    @property
    def short(self):
        return self.tr("short")

    @property
    def description(self):
        return self.tr("description")

    @property
    def visa(self):
        return self.tr("visa")

    @property
    def best_season(self):
        return self.tr("best_season")

    @property
    def has_info(self):
        return any([self.visa_ky, self.currency, self.flight_time, self.best_season_ky])

    @property
    def map_embed_url(self):
        from urllib.parse import quote

        query = self.map_query or self.name_ru
        return f"https://www.google.com/maps?q={quote(query)}&z=6&output=embed&hl={current_lang()}"

    def get_absolute_url(self):
        return reverse("tours:country", args=[self.slug])


class Photo(models.Model):
    """Өлкөнүн фотогалереясы."""

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="photos", verbose_name="Өлкө")
    image = models.ImageField("Сүрөт", upload_to="gallery/", blank=True)
    image_url = models.URLField("Сүрөттүн шилтемеси", max_length=500, blank=True)
    order = models.PositiveSmallIntegerField("Иреттик номер", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Сүрөт"
        verbose_name_plural = "Фотогалерея"

    def __str__(self):
        return f"{self.country} #{self.pk}"

    @property
    def url(self):
        if self.image:
            return self.image.url
        return self.image_url


class Hotel(TranslatedMixin, ImageMixin, models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="hotels", verbose_name="Өлкө")
    name = models.CharField("Аталышы", max_length=150)
    stars = models.PositiveSmallIntegerField("Жылдыз", default=4,
                                             validators=[MinValueValidator(1), MaxValueValidator(5)])
    price_per_night = models.DecimalField("Бир түнгө баасы (сом)", max_digits=10, decimal_places=0)
    description_ky = models.TextField("Сүрөттөмө (кырг.)", blank=True)
    description_ru = models.TextField("Сүрөттөмө (орус.)", blank=True)
    image = models.ImageField("Сүрөт", upload_to="hotels/", blank=True)
    image_url = models.URLField("Сүрөттүн шилтемеси", max_length=500, blank=True)
    is_active = models.BooleanField("Активдүү", default=True)

    class Meta:
        ordering = ["price_per_night"]
        verbose_name = "Мейманкана"
        verbose_name_plural = "Мейманканалар"

    def __str__(self):
        return f"{self.name} ({self.country})"

    @property
    def description(self):
        return self.tr("description")

    @property
    def stars_range(self):
        return range(self.stars)


class TourQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, country__is_active=True)

    def with_rating(self):
        return self.annotate(
            avg_rating=Avg("reviews__rating", filter=models.Q(reviews__is_approved=True)),
            reviews_count=Count("reviews", filter=models.Q(reviews__is_approved=True), distinct=True),
        )


class Tour(TranslatedMixin, ImageMixin, models.Model):
    TYPE_BEACH = "beach"
    TYPE_EXCURSION = "excursion"
    TYPE_SKI = "ski"
    TYPE_CITY = "city"
    TYPE_CHOICES = [
        (TYPE_BEACH, _("Пляж")),
        (TYPE_EXCURSION, _("Экскурсия")),
        (TYPE_SKI, _("Тоо лыжа")),
        (TYPE_CITY, _("Шаар")),
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="tours", verbose_name="Өлкө")
    title_ky = models.CharField("Аталышы (кырг.)", max_length=200)
    title_ru = models.CharField("Аталышы (орус.)", max_length=200)
    slug = models.SlugField("URL аты", unique=True, max_length=220)
    tour_type = models.CharField("Тур түрү", max_length=20, choices=TYPE_CHOICES, default=TYPE_EXCURSION)
    description_ky = models.TextField("Сүрөттөмө (кырг.)")
    description_ru = models.TextField("Сүрөттөмө (орус.)")
    program_ky = models.TextField("Программа (кырг.)", blank=True, help_text="Ар бир күн — жаңы сапта")
    program_ru = models.TextField("Программа (орус.)", blank=True, help_text="Каждый день — с новой строки")
    includes_ky = models.TextField("Баага кирет (кырг.)", blank=True, help_text="Ар бири жаңы сапта")
    includes_ru = models.TextField("Баага кирет (орус.)", blank=True, help_text="Каждый пункт с новой строки")
    price = models.DecimalField("Баасы, 1 кишиге (сом)", max_digits=10, decimal_places=0)
    old_price = models.DecimalField("Эски баасы (арзандатуу үчүн)", max_digits=10, decimal_places=0,
                                    null=True, blank=True)
    duration_days = models.PositiveSmallIntegerField("Узактыгы (күн)", default=7)
    max_people = models.PositiveSmallIntegerField("Бир брондоодо макс. киши", default=10)
    image = models.ImageField("Негизги сүрөт", upload_to="tours/", blank=True)
    image_url = models.URLField("Сүрөттүн шилтемеси", max_length=500, blank=True)
    is_hot = models.BooleanField("Ысык тур (башкы бетте)", default=False)
    is_active = models.BooleanField("Сайтта көрүнөт", default=True)
    created_at = models.DateTimeField("Түзүлгөн", auto_now_add=True)

    objects = TourQuerySet.as_manager()

    class Meta:
        ordering = ["-is_hot", "price"]
        verbose_name = "Тур"
        verbose_name_plural = "Турлар"

    def __str__(self):
        return self.title_ky

    @property
    def title(self):
        return self.tr("title")

    @property
    def description(self):
        return self.tr("description")

    @property
    def program_lines(self):
        return [line.strip() for line in self.tr("program").splitlines() if line.strip()]

    @property
    def includes_lines(self):
        return [line.strip() for line in self.tr("includes").splitlines() if line.strip()]

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(round((1 - self.price / self.old_price) * 100))
        return 0

    def get_absolute_url(self):
        return reverse("tours:detail", args=[self.slug])


class Review(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="reviews", verbose_name="Тур")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews",
                             verbose_name="Колдонуучу")
    rating = models.PositiveSmallIntegerField("Баа", validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField("Пикир", max_length=2000)
    is_approved = models.BooleanField("Жарыяланган", default=True)
    created_at = models.DateTimeField("Жазылган", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Пикир"
        verbose_name_plural = "Пикирлер"
        constraints = [
            models.UniqueConstraint(fields=["tour", "user"], name="one_review_per_user_per_tour"),
        ]

    def __str__(self):
        return f"{self.user} → {self.tour} ({self.rating}★)"


class ContactMessage(models.Model):
    """Байланыш формасынан келген билдирүүлөр."""

    name = models.CharField("Аты", max_length=100)
    phone = models.CharField("Телефон", max_length=30)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Билдирүү", max_length=2000)
    is_processed = models.BooleanField("Иштетилди", default=False)
    created_at = models.DateTimeField("Келген", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Байланыш билдирүүсү"
        verbose_name_plural = "Байланыш билдирүүлөрү"

    def __str__(self):
        return f"{self.name} — {self.phone}"


class Favorite(models.Model):
    """Колдонуучунун сактаган (жактырган) турлары."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites",
                             verbose_name="Колдонуучу")
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="favorites", verbose_name="Тур")
    created_at = models.DateTimeField("Кошулган", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Сакталган тур"
        verbose_name_plural = "Сакталган турлар"
        constraints = [models.UniqueConstraint(fields=["user", "tour"], name="unique_favorite")]

    def __str__(self):
        return f"{self.user} ♥ {self.tour}"


class Article(TranslatedMixin, ImageMixin, models.Model):
    """Блог: саякат кеңештери, виза боюнча маалымат ж.б."""

    title_ky = models.CharField("Аталышы (кырг.)", max_length=200)
    title_ru = models.CharField("Аталышы (орус.)", max_length=200)
    slug = models.SlugField("URL аты", unique=True, max_length=220)
    excerpt_ky = models.CharField("Кыскача (кырг.)", max_length=300, blank=True)
    excerpt_ru = models.CharField("Кыскача (орус.)", max_length=300, blank=True)
    body_ky = models.TextField("Текст (кырг.)", help_text="Абзацтарды бош сап менен бөлүңүз")
    body_ru = models.TextField("Текст (орус.)")
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="articles", verbose_name="Өлкө")
    image = models.ImageField("Сүрөт", upload_to="articles/", blank=True)
    image_url = models.URLField("Сүрөттүн шилтемеси", max_length=500, blank=True)
    is_published = models.BooleanField("Жарыяланган", default=True)
    views = models.PositiveIntegerField("Көрүүлөр", default=0, editable=False)
    created_at = models.DateTimeField("Түзүлгөн", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Макала"
        verbose_name_plural = "Макалалар (блог)"

    def __str__(self):
        return self.title_ky

    @property
    def title(self):
        return self.tr("title")

    @property
    def excerpt(self):
        return self.tr("excerpt")

    @property
    def body(self):
        return self.tr("body")

    def get_absolute_url(self):
        return reverse("tours:article", args=[self.slug])


class FAQ(TranslatedMixin, models.Model):
    question_ky = models.CharField("Суроо (кырг.)", max_length=255)
    question_ru = models.CharField("Суроо (орус.)", max_length=255)
    answer_ky = models.TextField("Жооп (кырг.)")
    answer_ru = models.TextField("Жооп (орус.)")
    order = models.PositiveSmallIntegerField("Иреттик номер", default=0)
    is_active = models.BooleanField("Көрүнөт", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Суроо-жооп"
        verbose_name_plural = "Суроо-жооптор (FAQ)"

    def __str__(self):
        return self.question_ky

    @property
    def question(self):
        return self.tr("question")

    @property
    def answer(self):
        return self.tr("answer")


class Subscriber(models.Model):
    """Жаңылыктарга / акцияларга жазылгандар."""

    email = models.EmailField("Email", unique=True)
    created_at = models.DateTimeField("Жазылган", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Жазылуучу"
        verbose_name_plural = "Жазылуучулар"

    def __str__(self):
        return self.email
