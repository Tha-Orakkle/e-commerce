from django.urls import path

from .api.v1.routes.product import (
    ProductView,
    ProductDetailView
)
from .api.v1.routes.product_image import ProductImageView, ProductImagesView

urlpatterns = [
    path('products/', ProductView.as_view(), name="products"),
    path('products/<str:id>/', ProductDetailView.as_view(), name="product"),
    path('product-image/<str:product_id>/', ProductImagesView.as_view(), name="product-images"),
    path('product-image/<str:product_id>/<str:image_id>/', ProductImageView.as_view(), name="product-image"),

]