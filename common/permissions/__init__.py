from .roles import (
    IsCustomer,
    IsCustomerOrShopOwner,
    IsSuperUser,
    IsShopOwner,
    IsStaffSelfOrShopOwnerOrSuperuser
)

__all__ = [
    'IsCustomer',
    'IsSuperUser',
    'IsShopOwner',
    'IsStaffSelfOrShopOwnerOrSuperuser',
    'IsCustomerOrShopOwner',
]