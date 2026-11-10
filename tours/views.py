from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from bookings.forms import BookingForm

from .forms import ContactForm, ReviewForm, SubscribeForm, TourFilterForm
from .models import FAQ, Article, Country, Favorite, Review, Subscriber, Tour
from .notify import notify_manager


def home(request):
    tours = Tour.objects.active().with_rating().select_related("country")
    context = {
        "countries": Country.objects.filter(is_active=True),
        "hot_tours": tours.filter(is_hot=True)[:6] or tours[:6],
        "filter_form": TourFilterForm(),
        "stats": {
            "countries": Country.objects.filter(is_active=True).count(),
            "tours": Tour.objects.active().count(),
            "reviews": Review.objects.filter(is_approved=True).count(),
        },
        "latest_reviews": Review.objects.filter(is_approved=True).select_related("user", "tour")[:3],
        "articles": Article.objects.filter(is_published=True)[:3],
        "faqs": FAQ.objects.filter(is_active=True)[:6],
    }
    return render(request, "tours/home.html", context)


def tour_list(request):
    form = TourFilterForm(request.GET or None)
    tours = Tour.objects.active().with_rating().select_related("country")

    if form.is_valid():
        data = form.cleaned_data
        if data.get("q"):
            q = data["q"].strip()
            tours = tours.filter(
                Q(title_ky__icontains=q) | Q(title_ru__icontains=q)
                | Q(description_ky__icontains=q) | Q(description_ru__icontains=q)
                | Q(country__name_ky__icontains=q) | Q(country__name_ru__icontains=q)
            )
        if data.get("country"):
            tours = tours.filter(country=data["country"])
        if data.get("tour_type"):
            tours = tours.filter(tour_type=data["tour_type"])
        if data.get("price_min") is not None:
            tours = tours.filter(price__gte=data["price_min"])
        if data.get("price_max") is not None:
            tours = tours.filter(price__lte=data["price_max"])
        sort = data.get("sort")
        if sort in ("price", "-price"):
            tours = tours.order_by(sort)
        elif sort == "rating":
            tours = tours.order_by(F("avg_rating").desc(nulls_last=True), "price")
        elif sort == "new":
            tours = tours.order_by("-created_at")

    page = Paginator(tours, 9).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return render(request, "tours/tour_list.html", {
        "form": form if form.is_bound else TourFilterForm(),
        "page": page,
        "querystring": query.urlencode(),
    })


def country_detail(request, slug):
    country = get_object_or_404(Country, slug=slug, is_active=True)
    return render(request, "tours/country_detail.html", {
        "country": country,
        "tours": country.tours.active().with_rating(),
        "hotels": country.hotels.filter(is_active=True),
        "photos": country.photos.all(),
        "articles": country.articles.filter(is_published=True)[:3],
    })


def tour_detail(request, slug):
    tour = get_object_or_404(Tour.objects.active().with_rating().select_related("country"), slug=slug)
    reviews = tour.reviews.filter(is_approved=True).select_related("user")
    user_review = None
    if request.user.is_authenticated:
        user_review = tour.reviews.filter(user=request.user).first()
    context = {
        "tour": tour,
        "reviews": reviews,
        "review_form": ReviewForm(instance=user_review),
        "user_review": user_review,
        "booking_form": BookingForm(tour=tour, initial=_booking_initial(request)),
        "hotels": tour.country.hotels.filter(is_active=True),
        "photos": tour.country.photos.all()[:6],
        "similar": Tour.objects.active().with_rating().select_related("country")
                   .filter(country=tour.country).exclude(pk=tour.pk)[:3],
    }
    return render(request, "tours/tour_detail.html", context)


def _booking_initial(request):
    if not request.user.is_authenticated:
        return {}
    user = request.user
    return {"full_name": user.get_full_name() or user.username, "email": user.email}


@login_required
@require_POST
def review_create(request, slug):
    tour = get_object_or_404(Tour.objects.active(), slug=slug)
    existing = tour.reviews.filter(user=request.user).first()
    form = ReviewForm(request.POST, instance=existing)
    if form.is_valid():
        review = form.save(commit=False)
        review.tour = tour
        review.user = request.user
        review.save()
        messages.success(request, _("Пикириңиз үчүн рахмат!"))
    else:
        messages.error(request, _("Пикирди сактоо мүмкүн болгон жок: баа жана текст керек."))
    return redirect(tour.get_absolute_url() + "#reviews")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        msg = form.save()
        notify_manager(f"Жаңы билдирүү: {msg.name}",
                       f"{msg.name}, {msg.phone}, {msg.email or '—'}\n\n{msg.message}")
        messages.success(request, _("Билдирүүңүз жөнөтүлдү. Биз сиз менен жакында байланышабыз!"))
        return redirect("tours:contact")
    return render(request, "tours/contact.html", {"form": form})


def about(request):
    return render(request, "tours/about.html")


def _safe_next(request, default):
    url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
        return url
    return default


@login_required
@require_POST
def favorite_toggle(request, slug):
    tour = get_object_or_404(Tour.objects.active(), slug=slug)
    fav, created = Favorite.objects.get_or_create(user=request.user, tour=tour)
    if not created:
        fav.delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"saved": created})
    return redirect(_safe_next(request, tour.get_absolute_url()))


def article_list(request):
    articles = Article.objects.filter(is_published=True).select_related("country")
    page = Paginator(articles, 9).get_page(request.GET.get("page"))
    return render(request, "tours/article_list.html", {"page": page})


def article_detail(request, slug):
    article = get_object_or_404(Article.objects.select_related("country"), slug=slug, is_published=True)
    Article.objects.filter(pk=article.pk).update(views=F("views") + 1)
    related_tours = (Tour.objects.active().with_rating().select_related("country")
                     .filter(country=article.country)[:3] if article.country else [])
    others = Article.objects.filter(is_published=True).exclude(pk=article.pk)[:3]
    return render(request, "tours/article_detail.html", {
        "article": article, "related_tours": related_tours, "others": others,
    })


def faq(request):
    return render(request, "tours/faq.html", {"faqs": FAQ.objects.filter(is_active=True)})


@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    if form.is_valid():
        Subscriber.objects.get_or_create(email=form.cleaned_data["email"].lower())
        messages.success(request, _("Рахмат! Сиз акцияларга жазылдыңыз."))
    else:
        messages.error(request, _("Email дарегин туура жазыңыз."))
    return redirect(_safe_next(request, "/"))
