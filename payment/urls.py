from django.urls import path

from .api.v1.services.initialize_paystack import InitializePaymentView
from .api.v1.services.verify_paystack import VerifyPaymentView


urlpatterns = [
    path('payment/initialize/', InitializePaymentView.as_view(), name='initialize-payment'),
    path('payment/verify/', VerifyPaymentView.as_view(), name='verify-payment')
]