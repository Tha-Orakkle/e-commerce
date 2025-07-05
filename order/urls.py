from django.urls import path

from order.api.v1.routes.checkout import CheckoutView
from order.api.v1.routes.order import (
    OrdersView,
    UserOrdersView,
    UserOrderView
)

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrdersView.as_view(), name='orders'),
    path('orders/user/', UserOrdersView.as_view(), name='user-orders'),
    path('orders/user/<str:order_id>/', UserOrderView.as_view(), name='user-order'),
]