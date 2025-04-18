from django.urls import path, include
from django.urls import path

from .api.v1.routes.refresh_tokens import SecureTokenRefreshView
from .api.v1.routes.admin import AdminUserRegistrationView, AdminUserLoginView
from .api.v1.routes.users import UsersView, UserView
from .api.v1.routes.login_register import RegisterView, LoginView
from .api.v1.routes.logout import LogoutView
from .api.v1.routes.verify_email import VerifyEmailView
# from .api.v1.routes.google_oauth import google_login, google_callback

urlpatterns = [
    # registration and tokens generation
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('token/refresh/', SecureTokenRefreshView.as_view(), name='token-refresh'),

    # admin creation and login
    path('admin/create/', AdminUserRegistrationView.as_view(), name='create-admin'),
    path('admin/login/', AdminUserLoginView.as_view(), name='admin-login'),
    

    # sign in with google
    # path('auth/google/login/', google_login),
    # path('auth/callback/google/', google_callback),

    # email address verification
    path('verify/', VerifyEmailView.as_view(), name='verify-email'),

    # User
    path('users/', UsersView.as_view(), name='users'),
    path('users/<str:id>/', UserView.as_view(), name='user'),
]