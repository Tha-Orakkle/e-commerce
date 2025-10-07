from .login import (
    admin_login_schema,
    customer_login_schema
)
from .login_register import (
    user_login_schema,
    user_registration_schema
)
from .logout import logout_schema
from .profile import update_user_profile_schema, user_profile_category_add_or_remove_schema
from .registration import (
    customer_registration_schema,
    shopowner_registration_schema,
    shop_staff_creation_schema
)
from .refresh_token import token_refresh_schema
from .reset_password import (
    forgot_password_schema,
    reset_password_confirm_schema
)
from .verify_email import verify_email_schema
from .customer import (
    get_customer_schema,
    get_customers_schema,
    delete_customer_schema
)
from .shopowner import (
    get_shopowner_schema,
    get_shopowners_schema
)
from .staff import (
    delete_shop_staff_member_schema,
    get_shop_staff_member_schema,
    get_shop_staff_members_schema,
    patch_shop_staff_member_schema
)
from .update_user import patch_user_schema

__all__ = [
    # registration
    'customer_registration_schema',
    'shopowner_registration_schema',
    
    # login
    'admin_login_schema',
    'customer_login_schema',
    
    # users
    'patch_user_schema',
    
    # customers
    'get_customer_schema',
    'get_customers_schema',
    'delete_customer_schema',
    
    # shop owners
    'get_shopowner_schema',
    'get_shopowners_schema',
    
    # staff
    'shop_staff_creation_schema',
    'delete_shop_staff_member_schema',
    'get_shop_staff_member_schema',
    'get_shop_staff_members_schema',
    'patch_shop_staff_member_schema',
    
    # users
    'user_login_schema',
    'user_registration_schema',
    'logout_schema',
    'update_user_profile_schema',

    # admin users
    'admin_user_login_schema',
    'admin_user_registration_schema',

    # user-category
    'user_profile_category_add_or_remove_schema',

    # forgot password
    'forgot_password_schema',
    'reset_password_confirm_schema',

    # refresh token
    'token_refresh_schema',
    
    # verify email
    'verify_email_schema'
]