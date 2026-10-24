from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


def validate_accuracy_confirmed(value):
    """Ensure that product information is explicitly confirmed as accurate."""
    if value is not True:
        raise ValidationError("You must confirm that the product information is accurate.")


class Product(models.Model):
    # A unique auto-generated ID for every product.
    product_id = models.AutoField(primary_key=True)

    # Product name, with surrounding whitespace removed on validation.
    name = models.CharField(max_length=200)

    # Product category/group, also normalized on validation.
    category = models.CharField(max_length=100)

    # Money value: non-negative, with cents precision.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    # Stock quantity cannot be negative.
    quantity_in_stock = models.PositiveIntegerField(default=0)

    # Required confirmation that the submitted information is accurate.
    information_accuracy_confirmed = models.BooleanField(
        default=False,
        verbose_name="confirmation of information accuracy",
        validators=[validate_accuracy_confirmed],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="product_price_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(quantity_in_stock__gte=0),
                name="product_quantity_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(information_accuracy_confirmed=True),
                name="product_accuracy_confirmed",
            ),
            models.CheckConstraint(
                condition=Q(name__gt=""),
                name="product_name_not_empty",
            ),
            models.CheckConstraint(
                condition=Q(category__gt=""),
                name="product_category_not_empty",
            ),
        ]

    def clean(self):
        """Normalize text fields and enforce field-level business rules."""
        super().clean()

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError({"name": "This field is required."})
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValidationError({"category": "This field is required."})

        # Normalize user-facing text without changing its meaning.
        self.name = self.name.strip()
        self.category = self.category.strip()

        if self.price is not None and self.price < 0:
            raise ValidationError({"price": "Price cannot be negative."})

        if not self.information_accuracy_confirmed:
            raise ValidationError(
                {
                    "information_accuracy_confirmed": (
                        "You must confirm that the product information is accurate."
                    )
                }
            )

    def save(self, *args, **kwargs):
        # Run model validation before normal saves, including text normalization.
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name