from django.db import models
from django.dispatch import receiver

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
    
    def add_to_cart(self, product, quantity):
        """
        Add an item to the cart.
        """
        # confirm whats left of the stock
        stock = product.inventory.stock
        if stock == 0:
            raise ErrorException(
                detail="Product out of stock.",
                code='out_of_stock'
            )
        quantity = stock if int(quantity) > stock else int(quantity)

        # check if product does not already exist in the cart
        cart_item, created = self.items.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity = quantity
            cart_item.save()

        return self

    def remove_from_cart(self, cart_item):
        """
        Remove an item from the cart.
        """
        cart_item.delete()
        return self
    
    def increment_item_quantity(self, item):
        item.quantity += 1
        if item.quantity > item.product.inventory.stock:
            raise ErrorException(
                detail=f"Insufficient stock. Only {item.product.inventory.stock} left.",
                code='insufficient_stock'
            )
        item.save()
        return self
    
    def decrement_item_quantity(self, item):
        if item.quantity == 0:
            raise ErrorException(
                detail="Cannot remove from item with zero quantity.",
                code='invalid_quantity'
            )
        item.quantity -= 1
        if item.quantity == 0:
            item.delete()
        else:
            item.save()
        return self


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    quantity = models.PositiveIntegerField(null=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_cart_product'
            )
        ]
        ordering = ['-updated_at']


    def __str__(self):
        """
        String representation of the CartItem instance.
        """
        return f"<CartItem: {self.id}> {self.product.name} - {self.quantity} items"
