from django.urls import path

from product.api.v1.routes import (
    CategoryListCreateView,
    CategoryDetailView,
    InventoryUpdateView,
    ProductDetailView,
    ProductListView,
    ProductCategoryUpdateView,
    ShopProductListCreateView,
    ProductImageDetailView,
    ProductImageListCreateView
)


urlpatterns = [
    # product urls
    path('products/', ProductListView.as_view(), name="product-list"),
    path('products/<str:product_id>/', ProductDetailView.as_view(), name="product-detail"),
    path('shops/<str:shop_id>/products/', ShopProductListCreateView.as_view(), name="shop-product-list-create"),
    
    # product image urls
    path('products/<str:product_id>/images/', ProductImageListCreateView.as_view(), name="product-image-list-create"),
    path('products/<str:product_id>/images/<str:image_id>/', ProductImageDetailView.as_view(), name="product-image-detail"),

    # category urls
    path('categories/', CategoryListCreateView.as_view(), name="category-list-create"),
    path('categories/<str:category_id>/', CategoryDetailView.as_view(), name="category-detail"),

    # product categories
    path('products/<str:product_id>/categories/', ProductCategoryUpdateView.as_view(), name="product-category-update"),
    path('products/<str:product_id>/inventory/', InventoryUpdateView.as_view(), name='inventory-update'),

]