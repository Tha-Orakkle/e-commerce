from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

import os
import uuid

from common.exceptions import ErrorException
from user.api.v1.serializers import ShopStaffCreationSerializer
from .utils.shop_code import generate_shop_code
from .utils.uploads import shop_logo_upload_path

User = get_user_model()


class Shop(models.Model):
    """
    Shop model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    name = models.CharField(max_length=40, unique=True, null=False)
    code = models.CharField(max_length=7, unique=True, blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to=shop_logo_upload_path, null=True)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owned_shop')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """
        Save the shop instance.
        """
        if not self.code:
            while True:
                code = generate_shop_code()
                if not Shop.objects.filter(code=code).exists():
                    self.code = code
                    break
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        """
        Delete a shop instance and associated logo from file system.
        """
        if self.logo and os.path.isfile(self.logo.path):
            os.remove(self.logo.path)
        super().delete(*args, **kwargs)
        
    def staff_id_exists(self, staff_id):
        """
        Check that staff already exists.
        """
        if staff_id:
            if staff_id == self.owner.staff_id:
                return True
            return self.staff_members.filter(staff_id=staff_id).exists()
        return False
    
    def get_staff_member(self, staff_id):
        """
        Get a specfic staff member by staff id.
        """
        if staff_id is not None:
            return self.staff_members.filter(staff_id=staff_id).first()
        return None
        