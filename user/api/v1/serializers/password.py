from rest_framework import serializers

from user.cores.validators import validate_password


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
        
        if self._target_user is None:
            raise AssertionError(
                "UpdatePasswordSerializer requires a `user` in context or a request with user."
            )
    
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
                raise serializers.ValidationError("Old password is incorrect.")
            
        return attrs

    def save(self, **kwargs):
        """
        Update user password.
        """
        new = self.validated_data['new_password']
        self._target_user.set_password(new)
        self._target_user.save(update_fields=['password'])
        return self._target_user
