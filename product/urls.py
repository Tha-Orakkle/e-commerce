from django.urls import path

from .api.v1.routes.category import CategoriesView, CategoryView
from .api.v1.routes.inventory import InventoryView
from .api.v1.routes.product import ProductView, ProductDetailView, ProductCategoryView
from .api.v1.routes.product_image import ProductImagesView, ProductImageView


urlpatterns = [
    path('products/', ProductView.as_view(), name="products"),
    path('products/<str:product_id>/', ProductDetailView.as_view(), name="product"),
    path('product-image/<str:product_id>/', ProductImagesView.as_view(), name="product-images"),
    path('product-image/<str:product_id>/<str:image_id>/', ProductImageView.as_view(), name="product-image"),

    # category urls
    path('categories/', CategoriesView.as_view(), name="categories"),
    path('categories/<str:category_id>/', CategoryView.as_view(), name="category"),

    # product categories
    path('product/<str:product_id>/categories/', ProductCategoryView.as_view(), name="product-categories"),
    path('product/<str:product_id>/inventory/', InventoryView.as_view(), name='inventory'),

]