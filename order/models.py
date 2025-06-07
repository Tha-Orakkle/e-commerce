from django.db import models

import uuid

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
    shipping_address = models.CharField(max_length=255)
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

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"<Order: {self.id}> {self.user.email} - {self.total_amount} - {self.status}"
        
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