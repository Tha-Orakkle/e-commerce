from django.utils.text import slugify
from rest_framework import serializers

from product.models import Category


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']

    def validate_name(self, value):
        """
        Validate that the category name does not already exist.
        """
        if Category.objects.filter(slug__iexact=slugify(value)).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value