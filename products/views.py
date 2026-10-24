from django.shortcuts import render

from .forms import ProductForm
from .models import Product


def home(request):
    """Show the home page."""
    return render(request, "products/home.html")


def product_submit(request):
    """Show and handle the product submission form."""
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            # Show a fresh, empty form after a successful submission
            form = ProductForm()
            return render(
                request,
                "products/product_form.html",
                {
                    "form": form,
                    "success": True,
                    "success_message": "Your product information has been successfully submitted.",
                },
            )
    else:
        form = ProductForm()

    return render(request, "products/product_form.html", {"form": form})


def product_list(request):
    """Show all saved products in a table."""
    products = Product.objects.all()
    return render(request, "products/product_list.html", {"products": products})