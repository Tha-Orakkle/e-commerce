from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """
    Grants permission to only super users.
    """
    def has_permission(self, request, view):
        """
        Checks if user is super user.
        """
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser)


class IsShopOwner(BasePermission):
    """
    Grants permission to only shop owners.
    """
    
    def has_permission(self, request, view):
        """
        Check if the user is a shop owner.
        """
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'is_shopowner', False)
        )


class IsStaff(BasePermission):
    """
    Grant permission to staff.
    """
    
    def has_permission(self, request, view):
        """
        Check if the user is a stafff.
        """
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'is_staff', False)
        )

    
class IsCustomer(BasePermission):
    """
    Grants permission to only customers.
    """
    
    def has_permission(self, request, view):
        """
        Check if authenticated user is a customer.
        """
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_customer
        )

class IsCustomerOrShopOwner(BasePermission):
    """
    Grants permission to customers and shopowners.
    Ordinary Staff does not have access.
    """
    
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        if user.is_customer or user.is_shopowner:
            return True
        
        return False
