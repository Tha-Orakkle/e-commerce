from django.urls import path, include
from django.urls import path

from .tokens import SecureTokenRefreshView
from .views import RegisterView, LoginView, UserView

urlpatterns = [
    # registration and tokens generation
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', SecureTokenRefreshView.as_view(), name='token_refresh'),

    # User
    path('users/', UserView.as_view(), name='user'),
    path('users/<str:id>/', UserView.as_view(), name='user'),

]