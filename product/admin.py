from django.contrib import admin

from .models import (
    Product,
    ProductImage,
    Category,
    Inventory
)

admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Category)
admin.site.register(Inventory)