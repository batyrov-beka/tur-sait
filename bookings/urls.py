from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("tour/<slug:slug>/", views.booking_create, name="create"),
    path("tour/<slug:slug>/price/", views.price_preview, name="price"),
    path("<int:pk>/", views.booking_detail, name="detail"),
    path("<int:pk>/cancel/", views.booking_cancel, name="cancel"),
]
