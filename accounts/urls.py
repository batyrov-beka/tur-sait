from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cabinet/", views.cabinet, name="cabinet"),
    path("profile/", views.profile_edit, name="profile"),
    path(
        "password/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url=reverse_lazy("accounts:password_done"),
        ),
        name="password_change",
    ),
    path("password/done/", auth_views.PasswordChangeDoneView.as_view(template_name="accounts/password_done.html"), name="password_done"),
]
