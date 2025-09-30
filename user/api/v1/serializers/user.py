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
        

class UserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=False)
    staff_handle = serializers.CharField(
        min_length=3,
        max_length=20,
        required=False,
        allow_blank=False
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the update user serializer.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self._user = request.user if request else None
        
        
    def validate_email(self, value):
        value = value.strip().lower()
        exists = User.objects.filter(email=value).first()
        if exists and exists != self._user:
            raise serializers.ValidationError("User with email already exists.")
        return value
    
    
    def validate_staff_handle(self, value):
        """
        Check that staff handle does not already exists in the shop.
        """
        value = value.strip().lower()
        if not self._user.is_shopowner:
            return None
        shop = self._user.owned_shop
        if shop.staff_handle_exists(value) and self._user.staff_handle != value:
            raise serializers.ValidationError("Staff member with staff handle already exists.")
        return value
    
    def validate(self, attrs):
        """
        Remove the staff handle from the attrs if the person making the
        request is not a shop owner.
        """
        if not self._user.is_shopowner:
            attrs.pop('staff_handle', None)
            if not attrs.get('email', ''):
                raise serializers.ValidationError({'email': ['This field is required.']})
        else:
            if not attrs.get('email', '') and not attrs.get('staff_handle', ''):
                raise serializers.ValidationError({
                    'non_field_errors': ["Either 'email' or 'staff_handle' is field is required."],
                })
        return attrs
    
    def save(self, **kwargs):
        """
        Save changes. Update user verified status if a new email is updated.
        """
        fields = []
        old_email = self._user.email
        old_staff_handle = self._user.staff_handle
        
        for k,v in self.validated_data.items():
            if (k == 'email' and v == old_email) or (k == 'staff_handle' and v == old_staff_handle):
                continue
            setattr(self._user, k, v)
            fields.append(k)
            
        if 'email' in self.validated_data and old_email != self._user.email:
            self._user.is_verified = False
            fields.append('is_verified')
            
        if fields:
            fields.append('updated_at')
            self._user.save(update_fields=fields)
        return self._user       
        