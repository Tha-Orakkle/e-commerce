from .customer import (
    get_customer_schema,
    get_customers_schema,
    delete_customer_schema
)
from .login import (
    staff_login_schema,
    customer_login_schema
)
from .logout import logout_schema

from .password import (
    forgot_password_schema,
    reset_password_confirm_schema,
    update_password_schema,
    update_staff_password_by_shopowner_schema
)
from .profile import (
    update_user_profile_schema,
    update_user_preferred_category_schema
)

from .refresh_token import token_refresh_schema
from .registration import (
    customer_registration_schema,
    shopowner_registration_schema,
    shop_staff_creation_schema
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
from .verify_email import verify_email_schema


__all__ = [
    # registration/creation
    'customer_registration_schema',
    'shopowner_registration_schema',
    'shop_staff_creation_schema',

    # login
    'staff_login_schema',
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
    'delete_shop_staff_member_schema',
    'get_shop_staff_member_schema',
    'get_shop_staff_members_schema',
    'patch_shop_staff_member_schema',
    
    # users
    'logout_schema',
    'update_user_profile_schema',

    # user-category
    'update_user_preferred_category_schema',

    # password
    'forgot_password_schema',
    'reset_password_confirm_schema',
    'update_password_schema',
    'update_staff_password_by_shopowner_schema',

    # refresh token
    'token_refresh_schema',
    
    # verify email
    'verify_email_schema'
]