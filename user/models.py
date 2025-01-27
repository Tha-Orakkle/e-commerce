from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField

import uuid

from .managers import UserManager

# Create your models here. 
    
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model where email is the
    unique identifier for authentication
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    email = models.EmailField(unique=True, null=False, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
        
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return f"<User: {self.id}> {self.email}"
    
    
class UserProfile(models.Model):
    """
    User Profile model. Connected to each user object.
    """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    telephone = PhoneNumberField()
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
