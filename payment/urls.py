from django.urls import path

from .api.v1.routes.webhook_paystack import PaystackWebhookView
from .api.v1.services.initialize_paystack import InitializePaymentView
from .api.v1.services.verify_payment import VerifyPaymentView, TempCallback


urlpatterns = [
    path('paystack/webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
    
    path('payment/initialize/', InitializePaymentView.as_view(), name='initialize-payment'),
    path('payment/verify/', VerifyPaymentView.as_view(), name='verify-payment'),

    # To be removed later
    # Temporary callback for testing payment verification
    path('payment/temporary-callback/', TempCallback.as_view(), name='temporary-callback'),
]