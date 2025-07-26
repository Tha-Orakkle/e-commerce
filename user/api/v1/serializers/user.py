from rest_framework import serializers

from user.models import User
from .profile import UserProfileSerializer

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        exclude = ['shop', 'last_login', 'groups', 'user_permissions']
        read_only_fields = [
            'id', 'is_staff', 'is_superuser',
            'is_customer', 'is_shopowner',
            'date_joined', 'profile'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }