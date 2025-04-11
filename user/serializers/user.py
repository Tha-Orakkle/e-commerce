from rest_framework import serializers

from user.models import User
from user.utils.password_validation import password_check
from .profile import UserProfileSerializer


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'staff_id', 'is_staff', 'is_active', 'is_superuser', 'date_joined', 'is_verified', 'password', 'profile']
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'date_joined', 'profile']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """
        Create a new user with the provided validated data.
        """
        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError('User with this email already exists.')
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.is_verified = False
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Update a user with the validated data
        """
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate_password(self, password):
        """
        Validate the password strength.
        """
        try:
            password_check(password)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return password
