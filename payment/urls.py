from django.urls import path

from .api.v1.services import InitializePaystackView
from .api.v1.routes import (
    VerifyPaymentView,
    PaystackWebhookView,
    TempCallback
)


urlpatterns = [
    path('paystack/webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
    
    path('order-groups/<str:order_group_id>/payment/initialize/', InitializePaystackView.as_view(), name='initialize-payment'),
    path('payment/verify/<str:reference>/', VerifyPaymentView.as_view(), name='verify-payment'),

    # To be removed later
    # Temporary callback for testing payment verification
    path('payment/temporary-callback/', TempCallback.as_view(), name='temporary-callback'),
]