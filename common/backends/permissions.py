from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsSuperUser(BasePermission):
    """
    Grants permission to only super users.
    """
    def has_permission(self, request, view):
        """
        Checks if user is super user.
        """
        return bool(request.user and request.user.is_superuser)
