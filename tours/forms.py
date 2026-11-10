from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage, Country, Review, Tour


class TourFilterForm(forms.Form):
    SORT_CHOICES = [
        ("", _("Сунушталган")),
        ("price", _("Арзаны алдында")),
        ("-price", _("Кымбаты алдында")),
        ("rating", _("Рейтинг боюнча")),
        ("new", _("Жаңылары")),
    ]

    q = forms.CharField(label=_("Издөө"), required=False,
                        widget=forms.TextInput(attrs={"placeholder": _("Тур же өлкө...")}))
    country = forms.ModelChoiceField(label=_("Өлкө"), queryset=Country.objects.none(), required=False,
                                     to_field_name="slug", empty_label=_("Бардык өлкөлөр"))
    tour_type = forms.ChoiceField(label=_("Тур түрү"), required=False,
                                  choices=[("", _("Бардык түрлөр"))] + Tour.TYPE_CHOICES)
    price_min = forms.IntegerField(label=_("Баасы, сомдон"), required=False, min_value=0,
                                   widget=forms.NumberInput(attrs={"placeholder": _("мин.")}))
    price_max = forms.IntegerField(label=_("сомго чейин"), required=False, min_value=0,
                                   widget=forms.NumberInput(attrs={"placeholder": _("макс.")}))
    sort = forms.ChoiceField(label=_("Иреттөө"), required=False, choices=SORT_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["country"].queryset = Country.objects.filter(is_active=True)
        # Өлкөнүн аты учурдагы тилде көрүнсүн
        self.fields["country"].label_from_instance = lambda obj: obj.name


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "text"]
        labels = {"rating": _("Баа"), "text": _("Пикириңиз")}
        widgets = {
            "rating": forms.RadioSelect(choices=[(i, str(i)) for i in range(5, 0, -1)]),
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": _("Тур тууралуу таасирлериңиз...")}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "phone", "email", "message"]
        labels = {
            "name": _("Атыңыз"),
            "phone": _("Телефон"),
            "email": _("Email"),
            "message": _("Билдирүү"),
        }
        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "+996 ...", "inputmode": "tel"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }


class SubscribeForm(forms.Form):
    email = forms.EmailField(label=_("Email"),
                             widget=forms.EmailInput(attrs={"placeholder": "email@example.com"}))
