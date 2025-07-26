from .registration import ShopOwnerRegistrationView, CustomerRegistrationView
from .create_staff import ShopStaffCreationView
from .login import AdminLoginView, CustomerLoginView


__all__ = [
    # registration views
    'ShopOwnerRegistrationView',
    'CustomerRegistrationView',
    
    # create staff views
    'ShopStaffCreationView',
    
    # login views
    'AdminLoginView',
    'CustomerLoginView',
]
