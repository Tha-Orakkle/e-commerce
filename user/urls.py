from django.urls import path

from .tokens import SecureTokenObtainPairView, SecureTokenRefreshView
from .views import (
    RegisterView,
    UserView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', SecureTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', SecureTokenRefreshView.as_view(), name='token_refresh'),

    path('users/', UserView.as_view(), name='user'),
    path('users/<str:id>/', UserView.as_view(), name='user'),

]