from django.urls import path

from order.api.v1.routes.checkout import CheckoutView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
]