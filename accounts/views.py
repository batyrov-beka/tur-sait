from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from tours.models import Tour

from .forms import ProfileForm, SignUpForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:cabinet")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, _("Кош келиңиз! Каттоо ийгиликтүү өттү."))
        next_url = request.GET.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)
        return redirect("accounts:cabinet")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def cabinet(request):
    bookings = request.user.bookings.select_related("tour__country", "hotel")
    reviews = request.user.reviews.select_related("tour")
    favorites = (Tour.objects.active().with_rating().select_related("country")
                 .filter(favorites__user=request.user))
    return render(request, "accounts/cabinet.html", {
        "bookings": bookings, "reviews": reviews, "favorites": favorites,
    })


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Маалыматтар сакталды."))
        return redirect("accounts:cabinet")
    return render(request, "accounts/profile_edit.html", {"form": form})
