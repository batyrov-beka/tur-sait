from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(label=_("Аты"), max_length=150)
    last_name = forms.CharField(label=_("Фамилиясы"), max_length=150, required=False)
    email = forms.EmailField(label=_("Email"))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Бул email менен колдонуучу катталган."))
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": _("Аты"), "last_name": _("Фамилиясы"), "email": _("Email")}
