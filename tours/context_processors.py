from django.conf import settings

from .models import Country, current_lang


def site_info(request):
    """Бардык шаблондордо жеткиликтүү: меню үчүн өлкөлөр жана байланыштар."""
    contacts = dict(settings.SITE_CONTACTS)
    contacts["address"] = contacts.get(f"address_{current_lang()}") or contacts.get("address_ky", "")
    fav_ids = set()
    if request.user.is_authenticated:
        fav_ids = set(request.user.favorites.values_list("tour_id", flat=True))
    return {
        "fav_ids": fav_ids,
        "SITE_NAME": settings.SITE_NAME,
        "CONTACTS": contacts,
        "nav_countries": Country.objects.filter(is_active=True).only("slug", "name_ky", "name_ru"),
    }
