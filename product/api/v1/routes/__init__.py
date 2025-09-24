from .category import CategoryDetailView, CategoryListCreateView
from .inventory import InventoryUpdateView
from .product import (
    ProductListView,
    ProductDetailView,
    ShopProductListCreateView,
    ProductCategoryUpdateView
)
from .product_image import ProductImageListCreateView, ProductImageDetailView


__all__ = [
    # product views
    'ProductListView',
    'ProductDetailView',
    'ShopProductListCreateView',

    # product image views
    'ProductImageListCreateView',
    'ProductImageDetailView',
    
    # category views
    'CategoryDetailView',
    'CategoryListCreateView',
    'ProductCategoryUpdateView',
    
    # inventory views
    'InventoryUpdateView',
]