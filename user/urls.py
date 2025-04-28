from django.urls import path, include
from django.urls import path

from .api.v1.routes.refresh_tokens import SecureTokenRefreshView
from .api.v1.routes.admin import (
    AdminUserRegistrationView, AdminUserLoginView,
    AdminsView, AdminView
)
from .api.v1.routes.users import UsersView, UserView
from .api.v1.routes.login_register import RegisterView, LoginView
from .api.v1.routes.logout import LogoutView
from .api.v1.routes.verify_email import VerifyEmailView
from .api.v1.routes.reset_password import (
    ForgotPasswordView, ResetPasswordConfirmView
)
# from .api.v1.routes.google_oauth import google_login, google_callback

urlpatterns = [
    # registration and tokens generation
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('token/refresh/', SecureTokenRefreshView.as_view(), name='token-refresh'),

    # email address verification
    path('verify/', VerifyEmailView.as_view(), name='verify-email'),

    # password reset
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password'),
    
    # admin creation and login
    path('admin/create/', AdminUserRegistrationView.as_view(), name='create-admin'),
    path('admin/login/', AdminUserLoginView.as_view(), name='admin-login'),

    
    # admin users
    path('admin/users/', AdminsView.as_view(), name='admin-users'),
    path('admin/users/<str:id>/', AdminView.as_view(), name='admin-user'),

    # sign in with google
    # path('auth/google/login/', google_login),
    # path('auth/callback/google/', google_callback),


    # users
    path('users/', UsersView.as_view(), name='users'),
    path('users/<str:id>/', UserView.as_view(), name='user'),

]