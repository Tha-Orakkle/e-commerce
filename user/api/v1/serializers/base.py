from django.contrib.auth import get_user_model
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from common.utils.bools import parse_bool
from user.cores.validators import validate_password

User = get_user_model()


class BaseUserCreationSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    # profile fields
    first_name = serializers.CharField(min_length=2, max_length=30)
    last_name = serializers.CharField(min_length=2, max_length=30)
    telephone = PhoneNumberField(
        required=False,
        allow_blank=True,
        region='NG',
    )
    
    def validate_password(self, value):
        """
        Validate the password.
        """
        already_user = parse_bool(self.initial_data.get(
            'already_customer', parse_bool(self.initial_data.get('already_shopowner', False))))
        if not already_user:
            # only validate when user not already a shop owner or a customer.
            # When already a user, user will be authenticated instead.
            validate_password(value)
        return value

    def validate_confirm_password(self, value):
        """
        Check that confirm password matches the password.
        """
        value = value.strip()
        pwd = self.initial_data.get('password', '').strip()
        if (pwd and pwd != value) or (value and not pwd):
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_telephone(self, value):
        """
        Normalize to E.164 (string) so downstream serializers/models get
        exactly what they expect.
        """
        if not value:
            return value

        try:
            return value.as_e164  # e.g. "+2348012345678
        except AttributeError:
            raise serializers.ValidationError("Enter a valid phone number.")
