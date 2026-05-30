from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "business_name",
            "first_name",
            "last_name",
            "title",
            "industry",
            "company_size",
            "revenue",
            "corporate_style",
        ]
        labels = {
            "business_name": "Business Name",
            "first_name": "First Name",
            "last_name": "Last Name",
            "company_size": "Company Size (Employees)",
            "corporate_style": "Corporate Style",
        }
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
