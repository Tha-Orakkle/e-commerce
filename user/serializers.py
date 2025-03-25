from rest_framework import serializers

from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'telephone']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'is_staff', 'is_active', 'is_superuser', 'date_joined', 'profile']
        read_only_fields = ['id', 'is_staff', 'is_active', 'date_joined']
        write_only_fields = ['password']