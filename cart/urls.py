from django.urls import path

from .api.v1.routes import (
    CartView   
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart')
]