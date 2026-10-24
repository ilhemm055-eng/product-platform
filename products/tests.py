from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from .models import Product


class ProductDataQualityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_data = {
            "name": "Widget",
            "category": "Gadgets",
            "price": "10.00",
            "quantity_in_stock": "5",
            "information_accuracy_confirmed": "on",
        }

    # --- Model and database validation ---

    def test_valid_product_is_saved_and_normalized(self):
        product = Product(
            name="  Widget  ",
            category="  Gadgets  ",
            price=Decimal("10.00"),
            quantity_in_stock=5,
            information_accuracy_confirmed=True,
        )
        product.save()

        stored = Product.objects.get(pk=product.pk)
        self.assertEqual(stored.name, "Widget")
        self.assertEqual(stored.category, "Gadgets")
        self.assertEqual(stored.price, Decimal("10.00"))
        self.assertEqual(stored.quantity_in_stock, 5)
        self.assertTrue(stored.information_accuracy_confirmed)

    def test_negative_price_is_rejected_by_model_validation(self):
        product = Product(
            name="Widget",
            category="Gadgets",
            price=Decimal("-1.00"),
            quantity_in_stock=5,
            information_accuracy_confirmed=True,
        )
        with self.assertRaises(ValidationError):
            product.save()

    def test_accuracy_confirmation_false_is_rejected_by_model_validation(self):
        product = Product(
            name="Widget",
            category="Gadgets",
            price=Decimal("10.00"),
            quantity_in_stock=5,
            information_accuracy_confirmed=False,
        )
        with self.assertRaises(ValidationError):
            product.save()

    def test_blank_or_whitespace_name_is_rejected(self):
        for value in ("", "   "):
            product = Product(
                name=value,
                category="Gadgets",
                price=Decimal("10.00"),
                quantity_in_stock=5,
                information_accuracy_confirmed=True,
            )
            with self.assertRaises(ValidationError):
                product.save()

    def test_blank_or_whitespace_category_is_rejected(self):
        for value in ("", "   "):
            product = Product(
                name="Widget",
                category=value,
                price=Decimal("10.00"),
                quantity_in_stock=5,
                information_accuracy_confirmed=True,
            )
            with self.assertRaises(ValidationError):
                product.save()

    def test_negative_quantity_is_rejected(self):
        product = Product(
            name="Widget",
            category="Gadgets",
            price=Decimal("10.00"),
            quantity_in_stock=-1,
            information_accuracy_confirmed=True,
        )
        with self.assertRaises(ValidationError):
            product.save()

    def test_zero_price_and_zero_stock_are_allowed(self):
        product = Product(
            name="Free Sample",
            category="Samples",
            price=Decimal("0.00"),
            quantity_in_stock=0,
            information_accuracy_confirmed=True,
        )
        product.save()
        self.assertEqual(Product.objects.count(), 1)

    def test_price_maximum_precision_is_enforced(self):
        valid = Product(
            name="Expensive",
            category="Luxury",
            price=Decimal("99999999.99"),
            quantity_in_stock=1,
            information_accuracy_confirmed=True,
        )
        valid.save()

        invalid = Product(
            name="Too Expensive",
            category="Luxury",
            price=Decimal("100000000.00"),
            quantity_in_stock=1,
            information_accuracy_confirmed=True,
        )
        with self.assertRaises(ValidationError):
            invalid.save()

    def test_duplicate_product_names_are_allowed(self):
        Product.objects.create(
            name="Widget",
            category="Gadgets",
            price=Decimal("10.00"),
            quantity_in_stock=5,
            information_accuracy_confirmed=True,
        )
        Product.objects.create(
            name="Widget",
            category="Other",
            price=Decimal("12.00"),
            quantity_in_stock=3,
            information_accuracy_confirmed=True,
        )
        self.assertEqual(Product.objects.count(), 2)

    # --- Database-level constraints (bypass model validation) ---

    def test_database_rejects_negative_price(self):
        with self.assertRaises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(
                        name="Widget",
                        category="Gadgets",
                        price=Decimal("-1.00"),
                        quantity_in_stock=5,
                        information_accuracy_confirmed=True,
                    )
                ]
            )

    def test_database_rejects_false_accuracy_confirmation(self):
        with self.assertRaises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(
                        name="Widget",
                        category="Gadgets",
                        price=Decimal("10.00"),
                        quantity_in_stock=5,
                        information_accuracy_confirmed=False,
                    )
                ]
            )

    def test_database_rejects_empty_name(self):
        with self.assertRaises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(
                        name="",
                        category="Gadgets",
                        price=Decimal("10.00"),
                        quantity_in_stock=5,
                        information_accuracy_confirmed=True,
                    )
                ]
            )

    def test_database_rejects_empty_category(self):
        with self.assertRaises(IntegrityError):
            Product.objects.bulk_create(
                [
                    Product(
                        name="Widget",
                        category="",
                        price=Decimal("10.00"),
                        quantity_in_stock=5,
                        information_accuracy_confirmed=True,
                    )
                ]
            )

    # --- Form and view behavior ---

    def test_valid_form_submission_saves_and_shows_success(self):
        response = self.client.post(reverse("product_submit"), self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Your product information has been successfully submitted."
        )
        self.assertEqual(Product.objects.count(), 1)

    def test_missing_required_fields_do_not_save(self):
        response = self.client.post(reverse("product_submit"), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertIn("name", response.context["form"].errors)
        self.assertIn("category", response.context["form"].errors)
        self.assertIn("price", response.context["form"].errors)
        self.assertIn("quantity_in_stock", response.context["form"].errors)
        self.assertIn("information_accuracy_confirmed", response.context["form"].errors)

    def test_negative_price_form_submission_is_invalid(self):
        data = dict(self.valid_data, price="-1.00")
        response = self.client.post(reverse("product_submit"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertIn("price", response.context["form"].errors)

    def test_false_accuracy_confirmation_form_submission_is_invalid(self):
        data = dict(self.valid_data)
        del data["information_accuracy_confirmed"]
        response = self.client.post(reverse("product_submit"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertIn("information_accuracy_confirmed", response.context["form"].errors)

    def test_invalid_data_types_are_rejected(self):
        data = dict(self.valid_data, price="not-a-number", quantity_in_stock="3.5")
        response = self.client.post(reverse("product_submit"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertIn("price", response.context["form"].errors)
        self.assertIn("quantity_in_stock", response.context["form"].errors)

    def test_whitespace_name_is_rejected_by_form(self):
        data = dict(self.valid_data, name="   ")
        response = self.client.post(reverse("product_submit"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertIn("name", response.context["form"].errors)

    def test_product_list_displays_saved_products(self):
        Product.objects.create(
            name="Listed Product",
            category="Category",
            price=Decimal("25.00"),
            quantity_in_stock=7,
            information_accuracy_confirmed=True,
        )
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Listed Product")
        self.assertContains(response, "25.00")
        self.assertContains(response, "7")