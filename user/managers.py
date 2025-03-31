from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class UserManager(BaseUserManager):
    """
    Custom manager for custom user model
    """

    def validate_and_normalize_email(self, email):
        """
        Validates and normalizes the email
        """
        if not email:
            raise ValidationError('The email field is required.')
        email = self.normalize_email(email).lower()
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError("The email address is invalid.")
        
        return email

    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with the given email and pasword
        """
        email = self.validate_and_normalize_email(email)

        if self.model.objects.filter(email=email).exists():
            raise ValueError("User with email already exists.")
        
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        """
        Create and return a superuser with all permissions
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
    
    def get_active_users(self):
        """
        Returns only active active users
        """
        return self.filter(is_active=True)

    def get_staff(self):
        """
        Returns users with is_staff=True
        """
        return self.filter(is_staff=True)


    def get_superuser(self):
        """
        Returns all superuser
        """
        return self.filter(is_superuser=True)
