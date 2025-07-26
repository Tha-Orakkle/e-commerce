from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """
    Grants permission to only super users.
    """
    def has_permission(self, request, view):
        """
        Checks if user is super user.
        """
        return bool(request.user and request.user.is_superuser)


class IsShopOwner(BasePermission):
    """
    Grants permission to only shop owners.
    """
    
    def has_permission(self, request, view):
        """
        Check if the user is a shop owner.
        """
        return bool(request.user.is_authenticated and getattr(request.user, 'is_shopowner', False))