from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "IT Travel — башкаруу"
admin.site.site_title = "IT Travel admin"
admin.site.index_title = "Башкаруу панели"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),  # тил которуу (set_language)
    path("accounts/", include("accounts.urls")),
    path("bookings/", include("bookings.urls")),
    path("", include("tours.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
