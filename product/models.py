from decimal import Decimal
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.apps import apps
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from io import BytesIO
from PIL import Image

import os
import uuid

from .utils.uploads import product_upload_image_path

IMAGE_SIZE = (800, 800)



class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=50, null=False, blank=False, unique=True)
    description = models.TextField(null=False, blank=False, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00), blank=False)

    def __str__(self):
        """
        Returns a string representation of the Product object.
        """
        return f"<Product: {self.id}> {self.name}"


    def get_image_path(self):
        """
        Return the upload path for product image.
        """
        from e_core.settings import MEDIA_ROOT
        product_image_dir = f'products/pdt_{self.id}'
        return MEDIA_ROOT / product_image_dir

    def add_images(self, images):
        """
        Adds product images to a product.
        """
        ProductImage = apps.get_model('product', 'ProductImage')
        for image in images:
            if not isinstance(image, InMemoryUploadedFile):
                continue
            ProductImage.objects.create(product=self, image=image)

    def delete_all_image_files(self):
        """
        Delete all associated image files.
        """
        import shutil

        path = self.get_image_path()
        if os.path.isdir(path):
            shutil.rmtree(path)

    def delete_images(self):
        """
        Deletes all images from db and associated files.
        """
        self.images.all().delete() # deletes from db
        self.delete_all_image_files() # delete associated files

    def update_images(self, images):
        """
        Updates the product images.
        """
        self.delete_images()
        self.add_images(images)

    def delete(self, *args, **kwargs):
        """
        Delete a Product instance.
        """
        super().delete(*args, **kwargs)
        self.delete_all_image_files()        


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    image = models.ImageField(upload_to=product_upload_image_path, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        """
        Returns a string representation of the ProductImage object.
        """
        return f"<ProductImage: {self.id}> {self.image}"
    
    def process_image(self, image):
        """
        Resize image to 800 x 800.
        """
        if image:
            img = Image.open(image)
            img.thumbnail(IMAGE_SIZE, Image.LANCZOS)
            bg = Image.new("RGB", IMAGE_SIZE, (255, 255, 255))
            offset = ((IMAGE_SIZE[0] - img.width) // 2, (IMAGE_SIZE[1] - img.height) // 2)
            bg.paste(img, offset)
            buffer = BytesIO()
            bg.save(buffer, format='JPEG', quality=95)
            buffer.seek(0)

            return InMemoryUploadedFile(
                file=buffer,
                field_name=getattr(image, 'field_name', None),
                name=image.name.rsplit('.', 1)[0] + '.jpg',
                content_type='image/jpeg',
                size=buffer.tell(),
                charset=getattr(image, 'charset', None)
            )
    
    def save(self, *args, **kwargs):
        """
        Save the ProductImage instance.
        """
        if self.image:
            self.image = self.process_image(self.image)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Delete the ProductImage instance.
        """
        if self.image:
            os.remove(self.image.path)
        super().delete(*args, **kwargs)


    
class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    quantity = models.PositiveIntegerField(default=0)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')

    def __str__(self):
        """
        Returns a string representation of the Inventory object.
        """
        return f"<Inventory: {self.id}> {self.product.name} - {self.quantity} items"



@receiver(sender=Product, signal=post_save)
def create_inventory(sender, instance, created, **kwargs):
    if created:
        Inventory.objects.create(product=instance)


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=20)
    products = models.ManyToManyField(Product, related_name='categories')

    def __str__(self):
        """
        Returns a string representation of the Category object.
        """
        return f"<Category: {self.id}> {self.name}"
    