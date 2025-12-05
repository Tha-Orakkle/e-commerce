from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework import serializers

from common.exceptions import ErrorException
from user.cores.validators import validate_password



class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, required=False, allow_blank=False)
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def __init__(self, *args, **kwargs):
        """
        Initialises the update password serializer.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self._actor_user = request.user if request else None
        self._target_user = self.context.get('user') or self._actor_user

    def validate_confirm_password(self, value):
        pwd = self.initial_data.get('new_password', '').strip()
        if pwd != value.strip():
            raise serializers.ValidationError("Passwords do not match.")
        return value
    
    def validate(self, attrs):
        """
        Require old_password unless the actor is a shopowner resetting a staff password.
        Return attrs unchanged if validation passes.
        """
        is_reset_by_shopowner = (
            self._actor_user
            and getattr(self._actor_user, 'is_shopowner', False)
            and getattr(self._target_user, 'is_staff', False)
        )
        
        if not is_reset_by_shopowner or (
            is_reset_by_shopowner and self._target_user == self._actor_user):
            old = attrs.get('old_password')
            if not old:
                raise serializers.ValidationError({'old_password': 'This field is required.'})
            if not self._target_user.check_password(old):
                raise serializers.ValidationError({'old_password': 'Old password is incorrect.'})
            
        return attrs

    def save(self, **kwargs):
        """
        Update user password.
        """
        new = self.validated_data['new_password']
        self._target_user.set_password(new)
        self._target_user.save(update_fields=['password'])
        return self._target_user


class ResetPasswordConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get('request', None)

        if not self.request:
            raise AssertionError("ResetPasswordConfirmSerializer requires request to be passed to context.")
    
    def _validate_passwords(self, pwd, c_pwd):
        if pwd != c_pwd:
            raise serializers.ValidationError({'non_field_error': 'Passwords do not match.'})
        return c_pwd
    
    def validate(self, attrs):
        self._validate_passwords(
            pwd=attrs.get('new_password', '').strip(),
            c_pwd=attrs.get('confirm_password', '').strip()
        )
        if not all(param in self.request.query_params for param in ['uid', 'token']):
            raise ErrorException(
                detail="Invalid or expired password reset link.",
                code='reset_failed'
            )
        attrs['uid'] = self.request.query_params.get('uid')
        attrs['token'] = self.request.query_params.get('token')
        return attrs
    
    def save(self, **kwargs):
        uid = self.validated_data.get('uid')
        token = self.validated_data.get('token')
        n_pwd = self.validated_data.get('new_password')
        token_gen = PasswordResetTokenGenerator()
        try:
            email = force_str(urlsafe_base64_decode(uid))
            User = get_user_model()
            user = User.objects.get(email=email)
            if not token_gen.check_token(user, token):
                raise ValueError()
        except:
            raise ErrorException(
                detail="Invalid or expired password reset link.",
                code='reset_failed'
            )
        
        user.set_password(n_pwd)
        user.save()
        return user
