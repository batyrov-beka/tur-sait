from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("tour/<slug:slug>/", views.booking_create, name="create"),
    path("tour/<slug:slug>/price/", views.price_preview, name="price"),
    path("<int:pk>/", views.booking_detail, name="detail"),
    path("<int:pk>/cancel/", views.booking_cancel, name="cancel"),
    path("<int:pk>/pay/", views.pay_start, name="pay"),
    path("payment/<int:payment_id>/test/", views.test_checkout, name="test_checkout"),
    path("payment/<int:payment_id>/return/", views.payment_return, name="payment_return"),
    path("payment/freedompay/result", views.freedompay_result, name="freedompay_result"),
]
