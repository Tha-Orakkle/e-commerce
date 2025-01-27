from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    """
    Custom manager for custom user model
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with the given email and pasword
        """
        if not email:
            raise ValueError("Email field must be set.")
        
        email = email.normalize_email(email)
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

    def get_active_users(self):
        """
        Returns users with is_staff=True
        """
        return self.filter(is_staff=True)


    def get_superuser(self):
        """
        Returns all superuser
        """
        return self.filter(is_superuser=True)
