from .login import (
    admin_login_schema,
    customer_login_schema
)

from .admin import (
    # delete_admin_user_schema,
    get_shop_staff_memeber_schema,
    get_shop_staff_schema,
    # update_admin_user_schema,
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
from .user import (
    delete_user_schema,
    get_user_schema,
    get_users_schema,
    update_user_schema
)
from .verify_email import verify_email_schema


__all__ = [
    # registration
    'customer_registration_schema',
    'shopowner_registration_schema',
    'shop_staff_creation_schema',
    
    # login
    'admin_login_schema',
    'customer_login_schema',
    
    # users
    'user_login_schema',
    'user_registration_schema',
    'delete_user_schema',
    'get_user_schema',
    'get_users_schema',
    'logout_schema',
    'update_user_profile_schema',
    'update_user_schema',

    # admin users
    'admin_user_login_schema',
    'admin_user_registration_schema',
    'delete_shop_staff_member_schema',
    'get_shop_staff_memeber_schema',
    'get_shop_staff_schema',
    'update_shop_staff_memmber_schema',

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