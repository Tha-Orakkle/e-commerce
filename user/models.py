import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework import status

from common.exceptions import ErrorException
from product.models import Category

from .managers import UserManager

# Create your models here.

MAX_PREFERRED_USER_CATEGORIES = 10


class UserSession(models.Model):
    """
    Represents one authenticated login session on one device.
    A user may have multiple independent sessions.
    """

    class RevocationReason(models.TextChoices):
        LOGOUT = "logout", "User logout"
        REFRESH_REUSE = "refresh_reuse", "Refresh token reuse detected"
        ACCOUNT_ACTION = "account_action", "Account security action"
        ADMIN = "admin", "Administrator revocation"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Absolute expiry of this login session.
    # Refreshing tokens must not extend this timestamp.
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(
        max_length=32,
        choices=RevocationReason.choices,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["user", "expires_at"]),
            models.Index(fields=["revoked_at", "expires_at"]),
        ]

    @property
    def is_active(self):
        return (
            self.revoked_at is None
            and self.expires_at > timezone.now()
        )

    def __str__(self):
        return f"Session {self.id}"

    def revoke(self, reason: RevocationReason):
        if self.revoked_at is None:
            self.revoked_at = timezone.now()
            self.revocation_reason = reason
            self.save(update_fields=["revoked_at", "revocation_reason"])


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model where email is the
    unique identifier for authentication
    """
    id = models.UUIDField(
        primary_key=True, editable=False,
        default=uuid.uuid4, unique=True, null=False
    )
    email = models.EmailField(unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    staff_handle = models.CharField(max_length=20, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_shopowner = models.BooleanField(default=False)
    # shop field stores where the user works if he is a staff at a shop
    shop = models.ForeignKey(
        'shop.Shop', null=True, blank=True,
        on_delete=models.CASCADE, related_name='staff_members'
    )
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    username = None

    objects = UserManager()
    USERNAME_FIELD = 'email'
    # just for the creation of super user
    REQUIRED_FIELDS = ['staff_handle']  # noqa: RUF012

    class Meta:
        ordering = ['-date_joined']  # noqa: RUF012

    def __str__(self):
        """
        Returns a string representation of the User object.
        Returns:
            str: A string in the format "<User: {self.id}> {self.email}".
        """
        role = (
            'Shopowner'
            if self.is_shopowner else 'Customer'
            if not self.is_staff else 'Shop_staff'
        )
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

    def can_manage_shop(self, shop):
        """
        Checks if a user can manage a particular shop.
        """
        return (
            self.is_superuser
            or (self.is_shopowner and self.owned_shop == shop)
            or (self.shop and self.shop == shop)
        )


class UserProfile(models.Model):
    """
    User Profile model. Connected to each user object.
    """
    id = models.UUIDField(
        primary_key=True, editable=False,
        default=uuid.uuid4, unique=True, null=False
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    telephone = PhoneNumberField()
    user = models.OneToOneField(
        User, related_name='profile',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    preferred_categories = models.ManyToManyField(
        'product.Category', blank=True)

    def __str__(self):
        """
        Returns a string representation of the UserProfile object.
        """
        return (
            f"<UserProfile: {self.id}> "
            f"\n\t FIRST NAME: {self.first_name} "
            f"\n\t LAST NAME: {self.last_name} "
            f"\n\t TELEPHONE: {self.telephone}"
        )

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
                detail=(
                    "Category with slug(s): "
                    f"\'{', '.join(missing_slugs)}\' not found."
                ),
                code='invalid_category',
                status_code=status.HTTP_404_NOT_FOUND
            )

        existing_ids = set(
            self.preferred_categories.values_list('id', flat=True)
        )
        new_categories = [
            c for c in found_categories if c.id not in existing_ids
        ]

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
