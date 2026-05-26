from django import forms


class FeedbackForm(forms.Form):
    report_feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Overall Feedback",
    )

    def __init__(self, *args, categories=None, **kwargs):
        super().__init__(*args, **kwargs)
        for category in categories or []:
            self.fields[f"category_{category.pk}"] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 3}),
                label=category.name,
            )

    def clean(self):
        cleaned_data = super().clean()
        has_content = any(
            v.strip() for v in cleaned_data.values() if isinstance(v, str) and v
        )
        if not has_content:
            msg = "Please provide at least one piece of feedback before submitting."
            raise forms.ValidationError(msg)
        return cleaned_data
