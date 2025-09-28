from django.urls import path

from order.api.v1.routes import (
    CheckoutView,
    CancelCustomerOrderGroupView,
    CustomerOrderGroupView,
    CustomerOrderGroupListView,
    ShopOrderView,
    ShopOrderDetailView,
    ShopOrderStatusUpdateView
)

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-groups/', CustomerOrderGroupListView.as_view(), name='user-groups'),
    path('order-groups/<str:order_group_id>/', CustomerOrderGroupView.as_view(), name='order-group'), 
    path('order-groups/<str:order_group_id>/cancel/', CancelCustomerOrderGroupView.as_view(), name='cancel-order'),
    
    path('shop/orders/', ShopOrderView.as_view(), name='orders'), # Get all orders for a shop
    path('shop/orders/<str:order_id>/', ShopOrderDetailView.as_view(), name='get-shop-order'),
    path('shop/orders/<str:order_id>/update-status/', ShopOrderStatusUpdateView.as_view(), name='update-order-status')
]