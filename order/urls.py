from django.urls import path

from order.api.v1.routes.cancel_order import CancelOrderView
from order.api.v1.routes.admin_update_order_status import AdminUpdateOrderStatus
from order.api.v1.routes import (
    CheckoutView,
    CustomerOrderGroupView,
    CustomerOrderGroupListView,
    ShopOrderView
)

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', ShopOrderView.as_view(), name='orders'), # Get all orders for a shop
    path('order-groups/', CustomerOrderGroupListView.as_view(), name='user-groups'),
    path('order-groups/<str:order_group_id>/', CustomerOrderGroupView.as_view(), name='order-group'), 
    
    path('orders/<str:order_id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    path('orders/<str:order_id>/update-status/', AdminUpdateOrderStatus.as_view(), name='update-order-status')
]