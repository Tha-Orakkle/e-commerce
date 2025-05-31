from django.db import models
from django.apps import apps
from django.dispatch import receiver
from django.db.models.signals import post_save

import uuid

from common.exceptions import ErrorException
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
    
    def add_item(self, product, quantity):
        """
        Add an item to the cart.
        """
        # confirm whats left of the stock
        stock = product.inventory.stock
        if stock == 0:
            raise ErrorException("Product out of stock.")
        quantity = stock if quantity > stock else quantity

        # check if product does not already exist in the cart
        item = self.items.filter(product__id=product.id).first()
        if item:
            item.quantity += quantity
            if item.quantity > stock:
                raise ErrorException("Product out of stock.")
            item.save()
        else:
            CartItem = apps.get_model('cart', 'CartItem')
            CartItem.objects.create(
                quantity=quantity,
                product=product,
                cart=self
            )
        return self



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
