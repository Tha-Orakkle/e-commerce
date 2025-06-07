from django.urls import path

from .api.v1.routes import (
    CartView,
    UpdateCartView
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/items/<str:cart_item_id>/', UpdateCartView.as_view(), name='update-cart-item')
]