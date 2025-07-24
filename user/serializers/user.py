from django.core.validators import validate_email as dj_validate_email
from django.contrib.auth import authenticate
from rest_framework import serializers
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.exceptions import ValidationError

from common.exceptions import ErrorException
from common.utils.bools import parse_bool
from shop.models import Shop
from user.models import User
from user.utils.password_validation import password_check
from .profile import UserProfileSerializer


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    profile = UserProfileSerializer(read_only=True)
    
    def __init__(self, *args, **kwargs):
        """
        Instantiates the  UserSerializer.
        """
        super().__init__(*args, **kwargs)
        self._shared_data = {
            'already_shopowner': parse_bool(self.context.get('already_shopowner', False)),
            'already_customer': parse_bool(self.context.get('already_customer', False)),
            'user_type': self.context.get('user_type', 'customer').strip().lower()
        }

    class Meta:
        model = User
        exclude = ['last_login', 'groups', 'user_permissions']
        read_only_fields = [
            'id', 'is_staff', 'is_superuser',
            'is_customer', 'is_shopowner',
            'date_joined', 'profile'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # def create(self, validated_data):
    #     """
    #     Create a new user with the provided validated data.
    #     """
    #     if User.objects.filter(email=validated_data['email']).exists():
    #         raise serializers.ValidationError('User with this email already exists.')
    #     password = validated_data.pop('password', None)
    #     user = User(**validated_data)
    #     user.set_password(password)
    #     user.is_active = True
    #     user.is_verified = False
    #     user.save()
    #     return user

    # def update(self, instance, validated_data):
    #     """
    #     Update a user with the validated data
    #     """
    #     password = validated_data.pop('password', None)
    #     if password:
    #         instance.set_password(password)
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
    #     instance.save()
    #     return instance

    def create(self, validated_data):
        """
        Create a new user depending on the context.
        Creates shop owners, staff and customers.
        """
        user_type = self._shared_data.get('user_type')
        already_shopowner = self._shared_data.get('already_shopowner')
        already_customer = self._shared_data.get('already_customer')
        
        if user_type == 'shopowner':
            user = self._create_shop_owner(
                validated_data, already_customer)
        elif user_type == 'customer':
            user = self._create_customer(
                validated_data, already_shopowner)   
        return user

    def _create_shop_owner(self, validated_data, already_customer):
        """
        Create a new shop owner or upgrade an existing customer
        account to a shop owner.
        """
        user = self.shared_data.get('user', None)
        
        if already_customer:
            user.is_shopowner = True
            user.is_staff = True
            user.staff_id = validated_data['staff_id']
            user.save()
        else:
            user = User.objects.create_shopowner(**validated_data)
        return user
        
    def _create_customer(self, validated_data, already_shopowner):
        """
        Create a new customer or upgrade an existing shopowner
        account to customer.
        """
        user = self.shared_data.get('user')
        if already_shopowner:
            user.is_customer = True
            user.save()
        else:
            user = User.object.create_user(**validated_data)
        return user

    def validate_email(self, value):
        already_shopowner = self._shared_data.get('already_shopowner')
        already_customer = self._shared_data.get('already_customer')
        user_type = self._shared_data.get('user_type')
        
        email = value.strip().lower()
        
        if not value:
            raise ValidationError("This field is required")
        try:
            dj_validate_email(email)
        except Exception:
            raise ValidationError("Enter a valid email address.")
        
        user = User.objects.filter(email=email).first()
        if user:
            self._shared_data['user'] = user
        if user_type == 'shopowner':
            if user and user.is_shopowner:
                raise ValidationError("Shop owner with email already exists.")            
            if user and not already_customer:
                raise ValidationError("User with email already exists.")
        elif user_type == 'customer':
            if user and user.is_customer:
                raise ValidationError("Customer with email already exists.")
            if user and not already_shopowner:
                raise ValidationError("User with email already exists.")
        return email
    
    
    def validate_staff_id(self, staff_id):
        """
        Validate the staff id.
        """
        user_type = self._shared_data.get('user_type')
        
        staff_id.strip().lower()
        if user_type == 'shopowner':
            if not staff_id:
                raise ValidationError("This field is required")
            if len(staff_id) < 3:
                raise ValidationError("Staff id must be at least 3 characters long.")
            if len(staff_id) > 20:
                raise ValidationError("Staff id must not be more than 20 characters.")
            return staff_id
        return None
    
    
    def validate_password(self, value):
        """
        Validate the password.
        """
        password = value.strip()
        if not password:
            raise ValidationError("This field is required.")
        errors = self.password_check(password)
        if errors:
            raise ValidationError(errors)
        return password


    def password_check(self, password):
        """
        Check the strength of the password.
        """
        error_list = []
        password = password.strip()

        if password and len(password) < 8:
            error_list.append("Password must be at least 8 characters long.")
        if password and not any(char.isdigit() for char in password):
            error_list.append("Password must contain at least one digit.")
        if password and not any(char.isalpha() for char in password):
            error_list.append("Password must contain at least one letter.")
        if password and not any(char.isupper() for char in password):
            error_list.append("Password must contain at least one uppercase letter.")
        if password and not any(char.islower() for char in password):
            error_list.append("Password must contain at least one lowercase letter.")
        if password and not any(char in ['@', '#', '$', '%', '^', '&', '*'] for char in password):
            error_list.append("Password must contain at least one special character.")
    
        return error_list
        
    
    def validate(self, attrs):
        """
        Validate all fields.
        """
        already_shopowner = self._shared_data.get('already_shopowner')
        already_customer = self._shared_data.get('already_customer')
        user_type = self._shared_data.get('user_type')
        user = self._shared_data.get('user', None)
        
        pwd = attrs.get('password', '').strip()
        c_pwd = self.initial_data.get('confirm_password', '').strip()
        
        if not self.instance:
            authenticated_user = user if user and user.check_password(pwd) else None
            if pwd != c_pwd:
                raise ValidationError({'password': 'Password and confirm password fields do not match.'})

            if user_type == 'shopowner' and already_customer and not authenticated_user:
                raise ValidationError("Invalid email or password for already existing shop owner.")
            if user_type == 'customer' and already_shopowner and not authenticated_user:
                raise ValidationError("Invalid email or password for already existing customer.")
            return attrs
            