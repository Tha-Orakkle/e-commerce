from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

import uuid
import pycountry

from common.exceptions import ErrorException
from user.models import User


class Country(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    name = models.CharField(max_length=30, null=False)
    code = models.CharField(max_length=2, unique=True, null=False)

    class Meta:
        verbose_name_plural = 'Countries'
        ordering = ['name']

    def __str__(self):
        """
        String representation of the State model.
        """
        return f"<Country: {self.id}> {self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        """
        Save a new Country instance.
        """
        if not self.name:
            raise ErrorException("Enter a valid country name.")
        country = pycountry.countries.get(name=self.name)
        if not country:
            raise ErrorException("Enter a valid country name")
        self.code = country.alpha_2
        super().save(*args, **kwargs)
    

class State(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    name = models.CharField(max_length=32, null=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        """
        String representation of the State model.
        """
        return f"<State: {self.id}> {self.name}"
    

class City(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    name = models.CharField(max_length=52, null=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')

    class Meta:
        verbose_name_plural = 'Cities'
        ordering = ['name']

    def __str__(self):
        """
        String representation of the State model.
        """
        return f"<City/Town: {self.id}> {self.name} - {self.state.name}"


class ShippingAddress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, null=False)
    full_name = models.CharField(max_length=32, null=False)
    telephone = PhoneNumberField(null=False)
    street_address = models.CharField(max_length=256, null=False)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=False)
    postal_code = models.CharField(max_length=20, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'ShippingAddresses'

    def __str__(self):
        """
        String representation of the ShippingAddress model.
        """
        return f"<ShippingAddress: {self.id}> {self.street_address}, {self.city}, {self.city.state.name}."
