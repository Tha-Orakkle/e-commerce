from django.db import models

import os
import uuid

from .utils.shop_code import generate_shop_code
from .utils.uploads import shop_logo_upload_path


class Shop(models.Model):
    """
    Shop model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    name = models.CharField(max_length=40, unique=True, null=False)
    code = models.CharField(max_length=7, unique=True, blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to=shop_logo_upload_path, null=True)
    owner = models.OneToOneField('user.User', on_delete=models.CASCADE, related_name='owned_shop')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        """
        String representation of the Shop instance.
        """
        return f"<Shop: {self.id}> {self.code} - '{self.name[:20]}'"
    
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
        
    def staff_handle_exists(self, staff_handle):
        """
        Check that staff already exists.
        """
        if staff_handle:
            if staff_handle == self.owner.staff_handle:
                return True
            return self.staff_members.filter(staff_handle=staff_handle).exists()
        return False
    
    def get_staff_member(self, id):
        """
        Get a staff member by ID.
        """
        if id is not None:
            return self.staff_members.filter(id=id).first()
        return None
    
    def get_staff_by_handle(self, handle):
        """
        Get a staff member by staff handle.
        """
        if handle is not None:
            return self.staff_members.filter(staff_handle=handle).first()
        return None
    
    def get_all_staff_members(self):
        """
        Get all staff members.
        This does not include the shop owner
        """
        return self.staff_members.all()
        