from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """
    Grants permission to only super users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)