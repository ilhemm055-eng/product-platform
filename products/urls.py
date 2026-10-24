from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("submit/", views.product_submit, name="product_submit"),
    path("products/", views.product_list, name="product_list"),
]