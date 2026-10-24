from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "price",
            "quantity_in_stock",
            "information_accuracy_confirmed",
        ]
        labels = {
            "information_accuracy_confirmed": "confirmation of information accuracy",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["information_accuracy_confirmed"].required = True

    def clean_name(self):
        # Normalize surrounding whitespace before model validation runs.
        return self.cleaned_data["name"].strip()

    def clean_category(self):
        return self.cleaned_data["category"].strip()