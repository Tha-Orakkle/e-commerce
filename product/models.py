from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import uuid


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0))
    categories = models.ManyToManyField('Category', related_name='products', blank=True)



    def __str__(self):
        """
        Returns a string representation of the Product object.
        """
        return f"<Product: {self.id}> {self.name}"


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    link = models.ImageField(upload_to='media/')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='image_links')

    def __str__(self):
        """
        Returns a string representation of the ProductImage object.
        """
        return f"<ProductImage: {self.id}> {self.link}"

    
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
    

    def __str__(self):
        """
        Returns a string representation of the Category object.
        """
        return f"<Category: {self.id}> {self.name}"
    