from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from uuid import uuid4

import pytest
import shutil

from product.models import Category, Product, ProductImage

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


@pytest.fixture
def category(db):
    """
    Create a category instance for testing.
    """
    return Category.objects.create(
        name="Test Category",
        slug="test-category"
    )


@pytest.fixture
def product(db, temp_media_root):
    """
    Create a product instance for testing.
    """
    return Product.objects.create(
        name="Test Product",
        description="This is a test product.",
        price=9.99,
    )


def create_fake_images(num):
    """
    Creates fake images for testing.
    """
    images = []
    for _ in range(num):
        img = Image.new("RGB", (100, 100), color="white")
        buffer = BytesIO()
        img.save(buffer, format="jpeg")
        buffer.seek(0)
        images.append(SimpleUploadedFile(
            name=f"image_{uuid4()}.jpg",
            content=buffer.read(),
            content_type="image/jpeg"
        ))
    return images



@pytest.fixture
def product_image(db, product):
    """
    Create a product image instance for testing.
    """
    return ProductImage.objects.create(
        image=create_fake_images(1)[0],
        product=product
    )


@pytest.fixture
def category(db):
    """
    Create a category instance for testing.
    """
    return Category.objects.create(name="Test Category")