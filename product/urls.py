from django.urls import path

from .api.v1.routes.inventory import InventoryView
from .api.v1.routes.product_image import ProductImagesView, ProductImageView

from product.api.v1.routes import (
    ProductDetailView,
    ProductListView,
    ShopProductListCreateView,
    CategoryListCreateView,
    CategoryDetailView,
    ProductCategoryView
)


urlpatterns = [
    path('products/', ProductListView.as_view(), name="product-list"),
    path('products/<str:product_id>/', ProductDetailView.as_view(), name="product-detail"),
    path('shops/<str:shop_id>/products/', ShopProductListCreateView.as_view(), name="shop-product-list-create"),
    path('product-image/<str:product_id>/', ProductImagesView.as_view(), name="product-images"),
    path('product-image/<str:product_id>/<str:image_id>/', ProductImageView.as_view(), name="product-image"),

    # category urls
    path('categories/', CategoryListCreateView.as_view(), name="category-list-create"),
    path('categories/<str:category_id>/', CategoryDetailView.as_view(), name="category-detail"),

    # product categories
    path('products/<str:product_id>/categories/', ProductCategoryView.as_view(), name="product-categories"),
    path('products/<str:product_id>/inventory/', InventoryView.as_view(), name='inventory'),

]