from django.utils.text import slugify
from decimal import Decimal
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.apps import apps
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from io import BytesIO
from PIL import Image

import os
import uuid

from .utils.uploads import product_upload_image_path
from common.exceptions import ErrorException
from shop.models import Shop


IMAGE_SIZE = (800, 800)
MAX_PRODUCT_CATEGORIES = 5


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=50, null=False, blank=False, unique=True)
    description = models.TextField(null=False, blank=False, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00), blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, related_name='products')
    categories = models.ManyToManyField('product.Category', related_name='products')
    

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        """
        Returns a string representation of the Product object.
        """
        return f"<Product: {self.id}> {self.name}"


    def add_categories(self, categories):
        """
        Add product to specific categories.
        Args:
            categories - List of names of categories.
        """
        slugs = [slugify(c) for c in categories]
        found_categories =  Category.objects.filter(slug__in=slugs)

        # missing categories
        found_slugs = {c.slug for c in found_categories}
        missing_slugs = set(slugs) - found_slugs
        
        existing_ids = self.categories.values_list('id', flat=True)
        remaining_slot = MAX_PRODUCT_CATEGORIES - len(existing_ids)

        new_categories = [c for c in found_categories if c.id not in existing_ids]
        if remaining_slot > 0:
            self.categories.add(*new_categories[:remaining_slot])
        
        # update this to make sure errors are thrown in the serializer.
        # Serializer validates the category lists and throws errors before
        # the product is created
        if missing_slugs:
            raise ErrorException(
                f"Category with slug(s): \'{', '.join(missing_slugs)}\' not found.",
                code=404
            )

    def remove_categories(self, categories):
        """
        Remove product from a specific category.
        Args:
            categories - List of names of categories.
        """
        slugs = [slugify(c) for c in categories]
        found_categories = Category.objects.filter(slug__in=slugs)
        self.categories.remove(*found_categories)
        
    def get_image_dir(self):
        """
        Return the upload path for product image.
        """
        from django.conf import settings
        shop_code = self.shop.code
        product_image_dir = f"{shop_code}/products/pdt_{self.id}"
        return settings.MEDIA_ROOT / product_image_dir

    def add_images(self, images):
        """
        Adds product images to a product.
        """
        ProductImage = apps.get_model('product', 'ProductImage')
        count = self.images.count()
        if (8 - count) <= 0: # a product can only have 8 images
            return
        for image in images[:8 - count]:
            if not isinstance(image, InMemoryUploadedFile) and not isinstance(image, TemporaryUploadedFile):
                continue
            ProductImage.objects.create(product=self, image=image)

    def delete_all_image_files(self):
        """
        Delete all associated image files.
        """
        import shutil

        _dir = self.get_image_dir()
        if os.path.isdir(_dir):
            shutil.rmtree(_dir)

    def delete_images(self):
        """
        Deletes all images from db and associated files.
        """
        self.images.all().delete()
        self.delete_all_image_files()

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
        self.delete_all_image_files()       
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Save a Product instance.
        """
        if self.price < 0:
            self.price = Decimal(0.00)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    image = models.ImageField(upload_to=product_upload_image_path, null=False, max_length=255)
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
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)


class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    stock = models.PositiveIntegerField(default=0)
    last_updated_by = models.CharField(max_length=20)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')

    def __str__(self):
        """
        Returns a string representation of the Inventory object.
        """
        return f"<Inventory: {self.id}> {self.product.name} - {self.stock} items"
    
    def add(self, value, staff_id):
        if value <= 0:
            raise ErrorException("Provide a valid quantity that is greater than 0.")
        self.stock += value
        self.last_updated_by = staff_id
        self.save()
        return self
    
    def substract(self, value, staff_id):
        if value <= 0:
            raise ErrorException("Provide a valid quantity that is greater than 0.")
        self.stock -= value
        if self.stock < 0:
            raise ErrorException("Insufficient inventory.")
        self.last_updated_by = staff_id
        self.save()
        return self



@receiver(sender=Product, signal=post_save)
def create_inventory(sender, instance, created, **kwargs):
    if created:
        Inventory.objects.create(product=instance)


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=120, null=False, blank=False)
    slug = models.SlugField(max_length=150, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        """
        Returns a string representation of the Category object.
        """
        return f"<Category: {self.id}> {self.slug}"
    
    def save(self, *args, **kwargs):
        """
        Save the Category instance.
        """
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    