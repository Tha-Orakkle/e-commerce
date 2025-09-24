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
        slug_value = slugify(value)
        exists = Category.objects.filter(slug__iexact=slug_value).first()
        if self.instance:
            if exists and self.instance.slug != exists.slug:
                raise serializers.ValidationError("Category with this name already exists.")
        elif exists:
            raise serializers.ValidationError("Category with this name already exists.")
        return value.strip()