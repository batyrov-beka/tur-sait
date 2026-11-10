from django.contrib import admin

from .models import Booking, PromoCode


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "tour", "travel_date", "people_display", "total_price",
                    "status", "created_at")
    list_display_links = ("id", "full_name")
    list_editable = ("status",)
    list_filter = ("status", "tour__country", "travel_date", "created_at")
    search_fields = ("full_name", "phone", "email", "tour__title_ky", "tour__title_ru", "user__username")
    date_hierarchy = "created_at"
    readonly_fields = ("discount", "total_price", "created_at", "updated_at")
    autocomplete_fields = ("tour", "user")
    list_select_related = ("tour", "user")
    actions = ("mark_confirmed", "mark_paid", "mark_cancelled")
    fieldsets = (
        ("Тур", {"fields": ("tour", "hotel", "travel_date", "adults", "children", "promo", "discount", "total_price")}),
        ("Кардар", {"fields": ("user", "full_name", "phone", "email", "comment")}),
        ("Башкаруу", {"fields": ("status", "admin_note", "created_at", "updated_at")}),
    )

    @admin.display(description="Кишилер")
    def people_display(self, obj):
        return f"{obj.adults} + {obj.children}"

    def _set_status(self, request, queryset, status):
        for booking in queryset:
            booking.status = status
            booking.save()
        self.message_user(request, f"{queryset.count()} брондоо жаңыртылды.")

    @admin.action(description="Ырасталды деп белгилөө")
    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, Booking.STATUS_CONFIRMED)

    @admin.action(description="Төлөндү деп белгилөө")
    def mark_paid(self, request, queryset):
        self._set_status(request, queryset, Booking.STATUS_PAID)

    @admin.action(description="Жокко чыгаруу")
    def mark_cancelled(self, request, queryset):
        self._set_status(request, queryset, Booking.STATUS_CANCELLED)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "valid_until", "used_count", "max_uses", "is_active", "valid_now")
    list_editable = ("is_active",)
    search_fields = ("code",)
    readonly_fields = ("used_count",)

    @admin.display(description="Азыр иштейби", boolean=True)
    def valid_now(self, obj):
        return obj.is_valid
