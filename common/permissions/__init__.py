from .roles import (
    IsCustomer,
    IsCustomerOrShopOwner,
    IsSuperUser,
    IsShopOwner,
    IsStaff,
    IsStaffSelfOrShopOwnerOrSuperuser
)

__all__ = [
    'IsCustomer',
    'IsCustomerOrShopOwner',
    'IsSuperUser',
    'IsShopOwner',
    'IsStaff',
    'IsStaffSelfOrShopOwnerOrSuperuser',
]