from django.urls import path

from .api.v1.routes import (
    CartDetailView, 
    CartItemDetailView
)

urlpatterns = [
    path('customers/me/cart/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/items/<str:cart_item_id>/', CartItemDetailView.as_view(), name='cart-item-update')
]