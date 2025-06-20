from django.db import models

import uuid

from address.models import ShippingAddress
from product.models import Product
from user.models import User


class Order(models.Model):
    """
    Order model.
    """
    
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]

    FULFILLMENT_METHOD_CHOICES = [
        ('PICKUP', 'Pickup'),
        ('DELIVERY', 'Delivery')
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CASH_ON_DELIVERY', 'Cash on Delivery'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    DELIVERY_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('RETURNED', 'Returned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(choices=ORDER_STATUS_CHOICES, default='PENDING', max_length=12)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_address = models.CharField(max_length=255, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH_ON_DELIVERY')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    fulfillment_method = models.CharField(max_length=20, choices=FULFILLMENT_METHOD_CHOICES, default='DELIVERY')
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    processing_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)

    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True)
    # denormalized shipping details
    shipping_full_name = models.CharField(max_length=32)
    shipping_telephone = models.CharField(max_length=20)
    shipping_street_address = models.CharField(max_length=256)
    shipping_city = models.CharField(max_length=52)
    shipping_state = models.CharField(max_length=32)
    shipping_country = models.CharField(max_length=30)
    shipping_postal_code = models.CharField(max_length=20)
    

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"<Order: {self.id}> {self.user.email} - {self.total_amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        """
        Save the order instance.
        """
        if self.shipping_address:
            self.shipping_full_name = self.shipping_address.full_name
            self.shipping_telephone = str(self.shipping_address.telephone)
            self.shipping_street_address = self.shipping_address.street_address
            self.shipping_city = self.shipping_address.city.name
            self.shipping_state = self.shipping_address.city.state.name
            self.shipping_country = self.shipping_address.city.state.country.name
            self.shipping_postal_code = self.shipping_address.postal_code
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    OrderItem model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"<OrderItem: {self.id}> - {self.product.name} * {self.quantity}"