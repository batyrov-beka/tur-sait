from datetime import timedelta

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Booking, PromoCode


class BookingForm(forms.ModelForm):
    promo_code = forms.CharField(label=_("Промокод"), required=False, max_length=30,
                                 widget=forms.TextInput(attrs={"placeholder": "SUMMER10", "autocomplete": "off"}))

    class Meta:
        model = Booking
        fields = ["travel_date", "adults", "children", "hotel", "full_name", "phone", "email", "comment"]
        labels = {
            "travel_date": _("Учуу күнү"),
            "adults": _("Чоңдор"),
            "children": _("Балдар (12 жашка чейин)"),
            "hotel": _("Мейманкана"),
            "full_name": _("Аты-жөнүңүз"),
            "phone": _("Телефон"),
            "email": _("Email"),
            "comment": _("Кошумча каалоолор"),
        }
        widgets = {
            "travel_date": forms.DateInput(attrs={"type": "date"}),
            "adults": forms.NumberInput(attrs={"min": 1}),
            "children": forms.NumberInput(attrs={"min": 0}),
            "phone": forms.TextInput(attrs={"placeholder": "+996 ...", "inputmode": "tel"}),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, tour=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tour = tour
        min_date = timezone.localdate() + timedelta(days=3)
        self.fields["travel_date"].widget.attrs["min"] = min_date.isoformat()
        self.fields["hotel"].required = False
        self.fields["hotel"].empty_label = _("— Мейманканасыз —")
        if tour is not None:
            self.fields["hotel"].queryset = tour.country.hotels.filter(is_active=True)
            self.fields["adults"].widget.attrs["max"] = tour.max_people

    def clean_travel_date(self):
        date = self.cleaned_data["travel_date"]
        if date < timezone.localdate() + timedelta(days=3):
            raise forms.ValidationError(_("Учуу күнү бүгүндөн эң аз 3 күн кийин болушу керек."))
        return date

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) < 9:
            raise forms.ValidationError(_("Телефон номерин туура жазыңыз."))
        return phone

    def clean_promo_code(self):
        code = self.cleaned_data.get("promo_code", "").strip()
        if not code:
            return None
        promo = PromoCode.find_valid(code)
        if promo is None:
            raise forms.ValidationError(_("Промокод туура эмес же мөөнөтү бүткөн."))
        return promo

    def clean(self):
        cleaned = super().clean()
        adults = cleaned.get("adults") or 0
        children = cleaned.get("children") or 0
        if adults < 1:
            self.add_error("adults", _("Эң аз бир чоң адам болушу керек."))
        if self.tour and adults + children > self.tour.max_people:
            self.add_error("adults", _("Бир брондоодо эң көп %(n)s киши.") % {"n": self.tour.max_people})
        return cleaned
