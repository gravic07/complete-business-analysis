"""Forms for the public, unauthenticated client_portal application."""

from __future__ import annotations

from django import forms


class ClientEmailGateForm(forms.Form):
    """Collects the email used to verify a Client before granting link access."""

    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "input", "autofocus": "autofocus"}),
    )
