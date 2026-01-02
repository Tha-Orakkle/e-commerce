from .customer import CustomerListView, CustomerDetailView
from .login import ShopOwnerOrStaffLoginView, CustomerLoginView
from .registration import ShopOwnerRegistrationView, CustomerRegistrationView
from .shopowner import ShopOwnerListView, ShopOwnerDetailView
from .staff import ShopStaffListCreateView, ShopStaffDetailView
from .password import (
    ForgotPasswordView,
    ResetPasswordConfirmView,
    UpdatePasswordView,
    UpdateStaffPasswordByShopOwnerView
)
from .update_user import UpdateUserView


__all__ = [
    # registration views
    'ShopOwnerRegistrationView',
    'CustomerRegistrationView',
    
    # create staff views
    'ShopStaffCreationView',
    
    # update user
    'UpdateUserView',
    
    # login views
    'ShopOwnerOrStaffLoginView',
    'CustomerLoginView',
    
    # shop owners RUD views
    'ShopOwnerDetailView',
    'ShopOwnerListView',
    
    # shop staff members CRUD views
    'ShopStaffDetailView',
    'ShopStaffListCreateView',
    
    # customers RUD views
    'CustomerDetailView',
    'CustomerListView',
    
    # password
    'ForgotPasswordView',
    'ResetPasswordConfirmView',
    'UpdatePasswordView',
    'UpdateStaffPasswordByShopOwnerView',
]
