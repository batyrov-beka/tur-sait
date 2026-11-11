from django.urls import path

from . import views

app_name = "tours"

urlpatterns = [
    path("", views.home, name="home"),
    path("tours/", views.tour_list, name="list"),
    path("tours/<slug:slug>/", views.tour_detail, name="detail"),
    path("tours/<slug:slug>/review/", views.review_create, name="review"),
    path("countries/", views.country_list, name="countries"),
    path("countries/<slug:slug>/", views.country_detail, name="country"),
    path("tours/<slug:slug>/favorite/", views.favorite_toggle, name="favorite"),
    path("blog/", views.article_list, name="articles"),
    path("blog/<slug:slug>/", views.article_detail, name="article"),
    path("faq/", views.faq, name="faq"),
    path("terms/", views.legal_page, {"page": "terms"}, name="terms"),
    path("privacy/", views.legal_page, {"page": "privacy"}, name="privacy"),
    path("subscribe/", views.subscribe, name="subscribe"),
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),
]
