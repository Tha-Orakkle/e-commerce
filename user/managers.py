from django.contrib.auth.models import BaseUserManager
from django.core.validators import validate_email
from rest_framework.exceptions import ValidationError


class UserManager(BaseUserManager):
    """
    Custom manager for custom user model
    """

    def validate_and_normalize_email(self, email):
        """
        Validates and normalizes the email
        """
        if not email:
            raise ValueError("This field is required.")
        email = self.normalize_email(email).lower()
        try:
            validate_email(email)
        except Exception:
            raise ValueError("Enter a valid email address.")
        return email
        
    def create_user(self, email, password, **extra_fields):
        """
        Create a customer.
        """
        try:
            email = self.validate_and_normalize_email(email)
        except Exception as e:
            raise ValidationError({'email': [str(e)]})
        user = self.filter(email=email).first()
        if user and user.is_customer:
            raise ValidationError("Customer with email already exists.")
            
        if not user:
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
        user.is_active = True
        user.is_customer = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and return a superuser with all permissions
        """
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        extra_fields['is_verified'] = True
        extra_fields['is_shopowner'] = True
        
        return self.create_user(email, password, **extra_fields)
    
    def create_staff(self, shop, staff_id, password, **extra_fields):
        """
        Create staff with staff_id (username) and password.
        Email not required for the staff creation.
        """
        if shop.staff_id_exists(staff_id):
            raise ValidationError("Staff member with staff ID already exists.")
    
        extra_fields['is_active'] = True
        extra_fields['is_staff'] = True
        extra_fields['is_verified'] = True
        
        user = self.model(shop=shop, staff_id=staff_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_shopowner(self, email, staff_id, password, **extra_fields):
        """
        Create a shop owner with the email, staff_id (username), and password.
        """
        try:
            email = self.validate_and_normalize_email(email)
        except Exception as e:
            raise ValidationError({'email': [str(e)]})

        user = self.filter(email=email).first()
        if user and user.is_shopowner:
            raise ValidationError("Shop owner with email already exists")
    
        if not user:
            user = self.model(email=email)
            user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_shopowner = True
        user.staff_id = staff_id
        user.save(using=self._db)
        return user

    def get_superusers(self):
        """
        Returns all superuser
        """
        return self.filter(is_superuser=True)

    def get_active_users(self):
        """
        Returns only active active users
        """
        return self.filter(is_active=True, is_superuser=False)
    
    def get_shopowners(self):
        """
        Return all shop owners.
        """
        return self.filter(is_shopowner=True, is_superuser=False)

    def get_customers(self):
        """
        Return all customers.
        """
        return self.filter(is_customer=True, is_superuser=False)
