from django.contrib import admin
from django.utils.html import format_html

from .models import FAQ, Article, ContactMessage, Country, Favorite, Hotel, Photo, Review, Subscriber, Tour


def thumb(url, size=60):
    if not url:
        return "—"
    return format_html('<img src="{}" style="width:{}px;height:{}px;object-fit:cover;border-radius:6px">',
                       url, size, size)


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1
    fields = ("image", "image_url", "order", "preview")
    readonly_fields = ("preview",)

    @admin.display(description="Көрүнүшү")
    def preview(self, obj):
        return thumb(obj.url if obj.pk else "")


class HotelInline(admin.StackedInline):
    model = Hotel
    extra = 0
    fields = (("name", "stars", "price_per_night", "is_active"), ("image", "image_url"),
              "description_ky", "description_ru")


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("preview", "name_ky", "name_ru", "tours_count", "order", "is_active")
    list_display_links = ("preview", "name_ky")
    list_editable = ("order", "is_active")
    search_fields = ("name_ky", "name_ru")
    prepopulated_fields = {"slug": ("name_ru",)}
    inlines = [HotelInline, PhotoInline]
    fieldsets = (
        (None, {"fields": (("name_ky", "name_ru"), "slug", ("order", "is_active"))}),
        ("Текст", {"fields": ("short_ky", "short_ru", "description_ky", "description_ru")}),
        ("Пайдалуу маалымат", {"fields": (("visa_ky", "visa_ru"), ("currency", "flight_time"),
                                           ("best_season_ky", "best_season_ru"))}),
        ("Сүрөт жана карта", {"fields": ("image", "image_url", "map_query")}),
    )

    @admin.display(description="")
    def preview(self, obj):
        return thumb(obj.cover_url, 48)

    @admin.display(description="Турлар")
    def tours_count(self, obj):
        return obj.tours.count()


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ("preview", "title_ky", "country", "tour_type", "price", "duration_days", "is_hot", "is_active")
    list_display_links = ("preview", "title_ky")
    list_editable = ("price", "is_hot", "is_active")
    list_filter = ("country", "tour_type", "is_hot", "is_active")
    search_fields = ("title_ky", "title_ru", "description_ky", "description_ru")
    prepopulated_fields = {"slug": ("title_ru",)}
    list_select_related = ("country",)
    fieldsets = (
        (None, {"fields": ("country", ("title_ky", "title_ru"), "slug", "tour_type", ("is_hot", "is_active"))}),
        ("Баа жана шарттар", {"fields": (("price", "old_price"), ("duration_days", "max_people"))}),
        ("Сүрөттөмө", {"fields": ("description_ky", "description_ru", "program_ky", "program_ru",
                                  "includes_ky", "includes_ru")}),
        ("Сүрөт", {"fields": ("image", "image_url")}),
    )

    @admin.display(description="")
    def preview(self, obj):
        return thumb(obj.cover_url, 48)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "stars", "price_per_night", "is_active")
    list_filter = ("country", "stars", "is_active")
    list_editable = ("price_per_night", "is_active")
    search_fields = ("name",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("tour", "user", "rating", "short_text", "is_approved", "created_at")
    list_filter = ("is_approved", "rating", "tour__country")
    list_editable = ("is_approved",)
    search_fields = ("text", "user__username", "tour__title_ky")

    @admin.display(description="Пикир")
    def short_text(self, obj):
        return obj.text[:80]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at", "is_processed")
    list_filter = ("is_processed",)
    list_editable = ("is_processed",)
    search_fields = ("name", "phone", "email", "message")
    readonly_fields = ("created_at",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("preview", "title_ky", "country", "is_published", "views", "created_at")
    list_display_links = ("preview", "title_ky")
    list_filter = ("is_published", "country")
    list_editable = ("is_published",)
    search_fields = ("title_ky", "title_ru", "body_ky", "body_ru")
    prepopulated_fields = {"slug": ("title_ru",)}
    fieldsets = (
        (None, {"fields": (("title_ky", "title_ru"), "slug", "country", "is_published")}),
        ("Текст", {"fields": ("excerpt_ky", "excerpt_ru", "body_ky", "body_ru")}),
        ("Сүрөт", {"fields": ("image", "image_url")}),
    )

    @admin.display(description="")
    def preview(self, obj):
        return thumb(obj.cover_url, 48)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question_ky", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("question_ky", "question_ru")


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "tour", "created_at")
    list_filter = ("tour__country",)
