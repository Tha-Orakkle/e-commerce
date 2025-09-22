from django.urls import path

from .api.v1.routes import (
    CustomerDetailView,
    CustomerListView,
    CustomerLoginView,
    CustomerRegistrationView,
    ShopOwnerDetailView,
    ShopOwnerListView,
    ShopOwnerRegistrationView,
    ShopOwnerOrStaffLoginView,
    ShopStaffDetailView,
    ShopStaffListCreateView,
    ForgotPasswordView,
    ResetPasswordConfirmView,
    UpdatePasswordView,
    UpdateStaffPasswordByShopOwnerView,
    UpdateUserView
)
from .api.v1.routes.refresh_tokens import SecureTokenRefreshView

from .api.v1.routes.logout import LogoutView
from .api.v1.routes.verify_email import VerifyEmailView
from .api.v1.routes.profile import UserProfileView, UserProfileCategoryView
# from .api.v1.routes.google_oauth import google_login, google_callback

urlpatterns = [
    # customers auth
    path('auth/customers/register/', CustomerRegistrationView.as_view(), name='customer-register'),
    path('auth/customers/login/', CustomerLoginView.as_view(), name='customer-login'),
    
    # shop owners auth
    path('auth/shops/register/', ShopOwnerRegistrationView.as_view(), name='shopowner-register'),
    path('auth/staff/login/', ShopOwnerOrStaffLoginView.as_view(), name='staff-login'),

    # others
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', SecureTokenRefreshView.as_view(), name='token-refresh'),

    # email address verification
    path('verify/', VerifyEmailView.as_view(), name='verify-email'),

    # password
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('users/me/password/', UpdatePasswordView.as_view(), name='user-me-password'),
    path('shops/<str:shop_code>/staff/<str:staff_id>/password/', UpdateStaffPasswordByShopOwnerView.as_view(), name='shop-staff-password'),
    
    # update user
    path('users/me/', UpdateUserView.as_view(), name='user-me-update'),

    # user profile
    path('users/me/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/me/profile/categories/', UserProfileCategoryView.as_view(), name='profile-categories'),
    
    # shop owners
    path('shopowners/', ShopOwnerListView.as_view(), name='shopowner-list'),
    path('shopowners/<str:shopowner_id>/', ShopOwnerDetailView.as_view(), name='shopowner-detail'),
    
    # staff members
    path('shops/<str:shop_code>/staff/', ShopStaffListCreateView.as_view(), name='shop-staff-list-create'),
    path('shops/<str:shop_code>/staff/<str:staff_id>/', ShopStaffDetailView.as_view(), name='shop-staff-detail'),

    # customers
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/<str:customer_id>/', CustomerDetailView.as_view(), name='customer-detail'),
    

    # sign in with google
    # path('auth/google/login/', google_login),
    # path('auth/callback/google/', google_callback),
    
    

]