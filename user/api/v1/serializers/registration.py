from django.contrib.auth import get_user_model
from rest_framework import serializers

from .profile import UserProfileSerializer
from common.exceptions import ErrorException
from common.utils.bools import parse_bool
from cart.models import Cart
from shop.models import Shop
from user.cores.validators import validate_password

User = get_user_model()

class ShopOwnerRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    staff_id = serializers.CharField(min_length=3, max_length=20)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    # profile fields
    first_name = serializers.CharField(min_length=2, max_length=30)
    last_name = serializers.CharField(min_length=2, max_length=30)
    telephone = serializers.CharField(required=False, allow_blank=True)
    
    # shop fields
    shop_name = serializers.CharField(min_length=3, max_length=40)
    shop_description = serializers.CharField(
        min_length=10, max_length=2000, required=False, allow_blank=True)
    already_customer = serializers.BooleanField(default=False)
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer.
        """
        super().__init__(*args, **kwargs)
        self._existing_user = None
        self._profile_validated = None
    
    
    def validate_email(self, value):
        """
        Validate the email address.
        """
        email = value.strip().lower()
        exists = User.objects.filter(email=email).first()
        if exists and not parse_bool(self.initial_data.get('already_customer', False)):
            raise serializers.ValidationError("User with email already exists.")
        if exists and exists.is_shopowner:
            raise serializers.ValidationError("Shop owner with email already exists.")
        self._existing_user = exists
        return email
    
    def validate_shop_name(self, value):
        """
        Validate the shop name.
        """
        value = value.strip()
        if Shop.objects.filter(name=value).exists():
            raise serializers.ValidationError("Shop with name already exists.")
        return value
    
    
    def validate(self, attrs):
        """
        Final validation
        """
        pwd = attrs['password']
        cpwd = attrs['confirm_password']
        if pwd != cpwd:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        
        profile_data = {
            'first_name': attrs.get('first_name'),
            'last_name': attrs.get('last_name'),
            'telephone': attrs.get('telephone')
        }
        
        profile_serializer = UserProfileSerializer(data=profile_data)
        profile_serializer.is_valid(raise_exception=True)
        self._profile_validated = profile_serializer.validated_data
        
        return attrs
    
    def create(self, validated_data):
        already_customer = validated_data.pop('already_customer')
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')
        
        profile_data = self._profile_validated
        
        shop_data = {
            'name': validated_data.pop('shop_name'),
            'description': validated_data.pop('shop_description')
        }
        if already_customer and not self._existing_user:
            raise ErrorException(
                detail="Shop owner registration failed.",
                code="invalid_credentials",
                errors={'non_field_errors': ['Invalid credentials matching any customer.']}
            )
        if already_customer and self._existing_user:
            user = self._existing_user
            if not user.check_password(password):
                raise ErrorException(
                    detail="Shop owner registration failed.",
                    code="invalid_credentials",
                    errors={'non_field_errors': ['Invalid credentials matching any customer.']}
                )
            user.is_shopowner = True
            user.is_staff = True
            user.staff_id = validated_data['staff_id']
            user.save()
        else:
            user = User.objects.create_shopowner(
                email=validated_data['email'],
                staff_id=validated_data['staff_id'],
                password=password,
                already_customer=False               
            )
        
        # create/update the profile
        if self._existing_user:
            profile_serializer = UserProfileSerializer(
                instance=user.profile,
                data=profile_data,
                partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
        else:
            UserProfileSerializer().create({**profile_data, 'user': user})    
        
        # create the shop
        shop = Shop.objects.create(owner=user, **shop_data)
        return shop
    
class CustomerRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    # profile fields
    first_name = serializers.CharField(min_length=2, max_length=30)
    last_name = serializers.CharField(min_length=2, max_length=30)
    telephone = serializers.CharField(required=False, allow_blank=True)
    
    already_shopowner = serializers.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer.
        """
        super().__init__(*args, **kwargs)
        self._existing_user = None
        self._profile_validated = None
    
    def validate_email(self, value):
        """
        Validate the email address.
        """
        email = value.strip().lower()
        exists = User.objects.filter(email=email).first()
        if exists and not parse_bool(self.initial_data.get('already_shopowner', False)):
            raise serializers.ValidationError("User with email already exists.")
        if exists and exists.is_customer:
            raise serializers.ValidationError("Shop owner with email already exists.")
        self._existing_user = exists
        return email
    
    def validate(self, attrs):
        """
        Final validation
        """
        pwd = attrs['password']
        cpwd = attrs['confirm_password']
        if pwd != cpwd:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        
        profile_data = {
            'first_name': attrs.get('first_name'),
            'last_name': attrs.get('last_name'),
            'telephone': attrs.get('telephone')
        }
        
        profile_serializer = UserProfileSerializer(data=profile_data)
        profile_serializer.is_valid(raise_exception=True)
        self._profile_validated = profile_serializer.validated_data
        
        return attrs
    
    def create(self, validated_data):
        already_shopowner = validated_data.pop('already_shopowner')
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')
        
        profile_data = self._profile_validated
        
        if already_shopowner and not self._existing_user:
            raise ErrorException(
                detail="Customer registration failed.",
                code="invalid_credentials",
                errors={'non_field_errors': ['Invalid credentials matching any shop owner.']}
            )
        if already_shopowner and self._existing_user:
            user = self._existing_user
            if not user.check_password(password):
                raise ErrorException(
                    detail="Customer registration failed.",
                    code="invalid_credentials",
                    errors={'non_field_errors': ['Invalid credentials matching any shop owner.']}
                )
            user.is_customer = True
            user.save()
        else:
            user = User.objects.create_user(
                email=validated_data['email'],
                password=password
            )
        
        # create/update the profile
        if self._existing_user:
            profile_serializer = UserProfileSerializer(
                instance=user.profile,
                data=profile_data,
                partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
        else:
            UserProfileSerializer().create({**profile_data, 'user': user})    
        
        # create a cart for the customer
        Cart.objects.create(owner=user)
        return user