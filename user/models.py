from django.db import models
from django.db.models import Q 
from django.utils.text import slugify
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework import status

import uuid

from .managers import UserManager
from common.exceptions import ErrorException
from product.models import Category

# Create your models here. 

MAX_PREFERRED_USER_CATEGORIES = 10

    
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model where email is the
    unique identifier for authentication
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4, unique=True, null=False)
    email = models.EmailField(unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    staff_handle = models.CharField(max_length=20, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_shopowner = models.BooleanField(default=False)
    # shop field stores where the user works if he is a staff at a shop
    shop = models.ForeignKey('shop.Shop', null=True, blank=True, on_delete=models.CASCADE, related_name='staff_members')
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    username = None

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['staff_handle'] # just for the creation of super user

    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        """
        Returns a string representation of the User object.
        Returns:
            str: A string in the format "<User: {self.id}> {self.email}".
        """
        role = 'Shopowner' if self.is_shopowner else 'Customer' if not self.is_staff else 'Shop_staff'
        return f"<User: {self.id}> {self.email or self.staff_handle} ({role})"
    
    def can_manage_product(self, product):
        """
        Checks if a user can manage a particular product.
        """
        shop = product.shop
        return (
            self.is_superuser
            or (self.is_shopowner and self.owned_shop == shop)
            or (self.shop and self.shop == shop)
        )
        
    
    
class UserProfile(models.Model):
    """
    User Profile model. Connected to each user object.
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4, unique=True, null=False)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    telephone = PhoneNumberField()
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    preferred_categories = models.ManyToManyField('product.Category', blank=True)

    def __str__(self):
        """
        Returns a string representation of the UserProfile object.
        Returns:
            str: A string in the format "<UserProfile: {self.id}> {self.user.email}".
        """
        return f"<UserProfile: {self.id}> \n\t FIRST NAME: {self.first_name} \n\t LAST NAME: {self.last_name} \n\t TELEPHONE: {self.telephone}"
    
    
    def add_categories(self, categories):
        """
        Adds a list of categories to the user preferred categories.
        Necessary for making recommendations.
        Args: categories (list)
        """
        slugs = [slugify(c) for c in categories]
        found_categories = list(Category.objects.filter(slug__in=slugs))

        found_slugs = {c.slug for c in found_categories}
        missing_slugs = set(slugs) - found_slugs

        if missing_slugs:
            raise ErrorException(
                detail=f"Category with slug(s): \'{', '.join(missing_slugs)}\' not found.",
                code='invalid_category',
                status_code=status.HTTP_404_NOT_FOUND
            )

        existing_ids = set(self.preferred_categories.values_list('id', flat=True))
        new_categories = [c for c in found_categories if c.id not in existing_ids]

        remaining_slot = MAX_PREFERRED_USER_CATEGORIES - len(existing_ids)
        if remaining_slot > 0:
            self.preferred_categories.add(*new_categories[:remaining_slot])
   

    def remove_categories(self, categories):
        """
        Removes categories from user's preferred categories.
        """
        slugs = [slugify(c) for c in categories]
        found_categories = Category.objects.filter(slug__in=slugs)
        self.preferred_categories.remove(*found_categories)
