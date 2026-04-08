from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["business_name", "first_name", "last_name", "title", "industry"]
        widgets = {
            "business_name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Business Name"},
            ),
            "first_name": forms.TextInput(
                attrs={"class": "input", "placeholder": "First Name"},
            ),
            "last_name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Last Name"},
            ),
            "title": forms.TextInput(
                attrs={"class": "input", "placeholder": "Title at Company"},
            ),
        }
