from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model

import uuid

from address.models import ShippingAddress
from product.models import Product
from shop.models import Shop

User = get_user_model()


class OrderGroupStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PARTIALLY_FULFILLED = 'PARTIALLY_FULFILLED', 'Partially Fulfilled'
    FULFILLED = 'FULFILLED', 'Fulfilled'
    CANCELLED = 'CANCELLED', 'Cancelled'


class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending',
    PROCESSING = 'PROCESSING', 'Processing'
    SHIPPED = 'SHIPPED', 'Shipped'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class PaymentMethod(models.TextChoices):
    DIGITAL = 'DIGITAL', 'Digital Payment'
    CASH = 'CASH', 'Cash Payment'
    
    
class FulFillmentMethod(models.TextChoices):
    PICKUP = 'PICKUP', 'Pickup'
    DELIVERY = 'DELIVERY', 'Delivery'


class OrderGroup(models.Model):
    """
    OrderGroup model.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    status = models.CharField(max_length=20, choices=OrderGroupStatus.choices, default=OrderGroupStatus.PENDING)
    payment_method = models.CharField(max_length=15, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fulfillment_method = models.CharField(max_length=9, choices=FulFillmentMethod.choices, default=FulFillmentMethod.PICKUP)
    # is_paid = models.BooleanField(default=False)
    
    # user data including denormalized data
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='order_groups')
    email = models.EmailField()
    full_name = models.CharField(max_length=60)
    
    # shipping address data including denormalized data
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True)
    shipping_full_name = models.CharField(max_length=32)
    shipping_telephone = models.CharField(max_length=20)
    shipping_street_address = models.CharField(max_length=256)
    shipping_city = models.CharField(max_length=52)
    shipping_state = models.CharField(max_length=32)
    shipping_country = models.CharField(max_length=30)
    shipping_postal_code = models.CharField(max_length=20)    
    
    # dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    
    def __str__(self):
        return f"<OrderGroup: {self.id}> {self.total_amount} - {self.status}"
    
    
    @property
    def is_paid(self):
        return all(order.is_paid for order in self.orders.all())
    
    
    def _denormalize_shipping_address(self):
        """
        Denormalize data in case the Shipping Address object is deleted.
        """
        if self.shipping_address:
            self.shipping_full_name = self.shipping_address.full_name
            self.shipping_telephone = str(self.shipping_address.telephone)
            self.shipping_street_address = self.shipping_address.street_address
            self.shipping_city = self.shipping_address.city.name
            self.shipping_state = self.shipping_address.city.state.name
            self.shipping_country = self.shipping_address.city.state.country.name
            self.shipping_postal_code = self.shipping_address.postal_code
            
    def _denormalize_user(self):
        """
        Denormalize data in case the User  object is deleted.
        """
        if self.user:
            self.email = self.user.email
            self.full_name = f"{self.user.profile.first_name} {self.user.profile.last_name}"
        
    def save(self, *args, **kwargs):
        self._denormalize_shipping_address()
        self._denormalize_user()
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    Order model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    group = models.ForeignKey(OrderGroup, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=12, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    is_paid = models.BooleanField(default=False)
    
    # shop and the denomalized data
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, related_name='orders')
    shop_name = models.CharField(max_length=40)
    
    is_delivered = models.BooleanField(default=False)
    is_picked_up = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    processing_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"<Order: {self.id}> - {self.total_amount} - {self.status}"

    def _denormalize_shop(self):
        """
        Denormalize data in case the shop object is deleted.
        """
        if self.shop:
            self.shop_name = self.shop.name
            

    def save(self, *args, **kwargs):
        self._denormalize_shop()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    OrderItem model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=50)
    product_description = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # product

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"<OrderItem: {self.id}> - {self.product.name} * {self.quantity}"
