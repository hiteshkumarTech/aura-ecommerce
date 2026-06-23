"""Forms for the store (checkout)."""
from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name", "email", "phone",
            "address", "city", "postal_code", "country",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Jane Doe", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "jane@example.com", "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": "+1 555 010 1234", "autocomplete": "tel"}),
            "address": forms.TextInput(attrs={"placeholder": "123 Market Street", "autocomplete": "street-address"}),
            "city": forms.TextInput(attrs={"placeholder": "San Francisco", "autocomplete": "address-level2"}),
            "postal_code": forms.TextInput(attrs={"placeholder": "94103", "autocomplete": "postal-code"}),
            "country": forms.TextInput(attrs={"placeholder": "United States", "autocomplete": "country-name"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Consistent styling hook for every field.
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " input").strip()
