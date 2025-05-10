from django.urls import path

from .api.v1.routes.product import ProductView

urlpatterns = [
    path('products/', ProductView.as_view(), name="products"),
]