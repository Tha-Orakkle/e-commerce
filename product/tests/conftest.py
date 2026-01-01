from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from uuid import uuid4

import pytest
import shutil

from product.models import Category, Product, ProductImage


def create_fake_images(n):
    """
    Creates fake images for testing.
    """
    images = []
    for _ in range(n):
        img = Image.new("RGB", (10, 10), color="white")
        buffer = BytesIO()
        img.save(buffer, format="jpeg")
        buffer.seek(0)
        images.append(SimpleUploadedFile(
            name=f"image_{uuid4()}.jpg",
            content=buffer.read(),
            content_type="image/jpeg"
        ))
    return images


def create_fake_files(n):
    """
    Create fake text files for testing.
    """

    files = []
    for i in range(n):
        f = SimpleUploadedFile(
            f"test{i}.txt",
            b"Test File",
            content_type='text/plain'
        )
        files.append(f)
    return files


@pytest.fixture(scope="module")
def shared_media_root(tmp_path_factory, request):
    tmp_path = tmp_path_factory.mktemp('media')

    # clean up
    def cleanup():
        if tmp_path.exists():
            shutil.rmtree(tmp_path)

    request.addfinalizer(cleanup)
    yield tmp_path


@pytest.fixture
def temp_media_root(shared_media_root, settings):
    settings.MEDIA_ROOT = shared_media_root

# FACTORIES

@pytest.fixture
def product_factory(db, temp_media_root):
    """
    Factory to create products.
    """
    def create_product(shop, name=None):
        # count = Product.objects.filter(shop_id=shop.id).count()
        count = Product.objects.count()
        name = name or f"Product {count}"
        return Product.objects.create(
            name=name,
            description=f"This is product {count}.",
            price=99.9,
            shop=shop
        )
    return create_product

@pytest.fixture
def product_image_factory(db, temp_media_root):
    """
    Factory to create product images.
    """
    
    def create_product_image(product):
        return ProductImage.objects.create(
            product=product,
            image=create_fake_images(1)[0]
        )
    return create_product_image

@pytest.fixture
def category_factory(db, temp_media_root):
    """
    Factory to create categories.
    """
    def create_category(name=None):
        count = Category.objects.count()
        name = name or f"Test Category {count}"
        return Category.objects.create(name=name)
    
    return create_category


@pytest.fixture
def product(db, shopowner, product_factory):
    """
    Create a product instance for testing.
    """
    return product_factory(shop=shopowner.owned_shop)

@pytest.fixture
def product_image(db, product, product_image_factory):
    """
    Create a product image instance for testing.
    """
    return product_image_factory(product=product)

@pytest.fixture
def category(db, category_factory):
    """
    Create a category instance for testing.
    """
    return category_factory()
