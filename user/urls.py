from django.urls import path, include
from django.urls import path

from .routes.refresh_tokens import SecureTokenRefreshView
from .routes.login_register import RegisterView, LoginView, UserView
from .routes.verify_email import VerifyEmailView
from .routes.google_oauth import google_login, google_callback

urlpatterns = [
    # registration and tokens generation
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', SecureTokenRefreshView.as_view(), name='token_refresh'),

    # sign in with google
    path('auth/google/login/', google_login),
    path('auth/callback/google/', google_callback),

    # email address verification
    path('verify/', VerifyEmailView.as_view(), name='verify_email'),

    # User
    path('users/', UserView.as_view(), name='user'),
    path('users/<str:id>/', UserView.as_view(), name='user'),
]