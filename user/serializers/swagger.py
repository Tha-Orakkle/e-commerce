from rest_framework import serializers

from common.swagger import BaseSuccessSerializer
from .user import UserSerializer


# SWAGGER UI REQUEST SERIALIZERS
# staff user
class AdminUserRegistrationRequestSerializer(serializers.Serializer):
    """
    Serializer for admin user registration requests.
    """
    staff_id = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

class AdminUserLoginRequestSerializer(serializers.Serializer):
    """
    Serializer for admin user login requests.
    """
    staff_id = serializers.CharField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField()

# regular user
class UserRegistrationRequestSerializer(serializers.Serializer):
    """
    Serializer for user registration requests.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

class UserLoginRequestSerializer(serializers.Serializer):
    """
    Serializer for user login requests.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField()



# SWAGGER UI RESPONSES SERIALIZERS
class RegistrationSuccessSerializer(BaseSuccessSerializer):
    """
    Serializer for successful user registration.
    """
    code = serializers.IntegerField(default=201)
    message = serializers.CharField(default='User registered successfully.')


class UserResponseSerializer(BaseSuccessSerializer):
    """
    Serializer for user data response.
    """
    data = UserSerializer()


class UserPaginatedResponseSerializer(serializers.Serializer):
    """
    Serializer for paginated users data.
    """
    results = UserSerializer(many=True)
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)


class UserListResponseSerializer(BaseSuccessSerializer):
    """
    Serializer for a list of users response.
    """
    data = UserPaginatedResponseSerializer()
