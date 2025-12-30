from django.db import transaction
from django.db.models import F, Q
from django.utils.text import slugify
from decimal import Decimal
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.apps import apps
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError
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
    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=False, blank=False, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00), blank=False)
    is_active = models.BooleanField(default=True, null=False)
    deactivated_at = models.DateTimeField(null=True, blank=True)
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
    
    @property
    def stock(self):
        return self.inventory._stock


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
                code='missing_categories'
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
        shp_id = self.shop.id
        product_image_dir = f"shp_{shp_id}/products/pdt_{self.id}"
        return settings.MEDIA_ROOT / product_image_dir

    def add_images(self, images):
        """
        Adds product images to a product.
        """
        from .api.v1.serializers import UploadProductImageSeriallizer

        serializers = UploadProductImageSeriallizer(
            data={'images': images},
            context={'product': self}
        )
        try:
            serializers.is_valid(raise_exception=True)
            serializers.save()
        except ValidationError:
            raise ErrorException(
                code='validation_error',
                detail="Could not add images to product.",
                errors=serializers.errors
            )
        

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
        
    def has_active_orders(self):
        """
        Return True if product has active orders.
        """
        from order.models import OrderStatus
        ACTIVE_ORDER_STATES = {
            OrderStatus.PENDING,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED
        }
        return self.orderitem_set.filter(
            order__status__in=ACTIVE_ORDER_STATES
        ).exists()

    def deactivate(self):
        self.is_active = False
        self.deactivated_at = now()
        self.save(update_fields=['is_active', 'deactivated_at'])

    def safe_delete(self):
        """
        Delete or deactivate products.
        """
        if self.has_active_orders():
            self.deactivate()
        else:
            self.delete()

    def delete(self, *args, **kwargs):
        """
        Delete a Product instance.
        """
        self.delete_images()
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
    _stock = models.PositiveIntegerField(default=0)
    last_updated_by = models.CharField(max_length=20)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def stock(self):
        return self._stock

    def __str__(self):
        """
        Returns a string representation of the Inventory object.
        """
        return f"<Inventory: {self.id}> {self.product.name} - {self.stock} items"

    @transaction.atomic
    def add(self, qty, handle):
        """
        Add to the stock.
        """
        if qty <= 0:
            raise ValueError("Provide a valid quantity that is greater than 0.")
        update_kwargs = {
            '_stock': F('_stock') + qty
        }
        if handle:
            update_kwargs['last_updated_by'] = handle
            
        (Inventory.objects
            .filter(id=self.id)
            .update(**update_kwargs))
        
        self.refresh_from_db(fields=['_stock', 'last_updated_by', 'updated_at'])
        return self    


    @transaction.atomic
    def subtract(self, qty, handle=None):
        """
        Subtract from the stock.
        """
        if qty <= 0:
            raise ValueError("Provide a valid quantity that is greater than 0.")
        update_kwargs = {
            '_stock': F('_stock') - qty,
        }
        if handle:
            update_kwargs['last_updated_by'] = handle
        updated = (
            Inventory.objects
                .filter(id=self.id, _stock__gte=qty)
                .update(**update_kwargs)
        )
        self.refresh_from_db(fields=['_stock', 'last_updated_by', 'updated_at'])
        if updated == 0:
            raise ErrorException(
                detail=f"Insufficient stock to complete this operation. Only {self._stock} left.",
                code='insufficient_stock'
            )
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
    