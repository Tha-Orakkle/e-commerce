from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

import uuid

from user.models import User
from product.models import Product

class Cart(models.Model):
    """
    Cart model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    
    def __str__(self):
        """
        String representation for the Cart instance.
        """
        return f"<Cart: {self.id}>"
    


@receiver(sender=User, signal=post_save)
def create_cart(sender, instance, created, **kwargs):
    """
    Creates a cart as soon as a user instance is created
    """
    if created:
        Cart.objects.create(user=instance)


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    quantity = models.PositiveIntegerField(null=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        """
        String representation of the CartItem instance.
        """
        return f"<CartItem: {self.id}> {self.product.name} - {self.quantity} items"
