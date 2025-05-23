from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

import os

from .conftest import create_fake_images
from product.models import Product, ProductImage, Category


def test_product_creation(product):
    """
    Test the creation of a product.
    """
    assert product.id is not None
    assert type(product.id).__name__ == "UUID"
    assert product.name == "Test Product"
    assert product.description == "This is a test product."
    assert product.price == 9.99


def test_product_str(product):
    """
    Test the string representation of a product.
    """
    assert str(product) == f"<Product: {product.id}> {product.name}"


def test_get_image_dir(product):
    """
    Test the image directory path for a product.
    """
    from django.conf import settings
    product_image_dir = f'products/pdt_{product.id}'
    assert product.get_image_dir() == settings.MEDIA_ROOT / product_image_dir


def test_add_images(product):
    """
    Test that multiple images are added to a product instance.
    """

    assert product.images.count() == 0
    assert not product.get_image_dir().exists()

    product.add_images(create_fake_images(2))

    assert product.images.count() == 2
    assert product.get_image_dir().exists()
    assert any(product.get_image_dir().iterdir()) # check that product images dir is not empty 


def test_delete_all_images(product):
    """
    Test deletion of all images of a product and associated files.
    """
    product.add_images(create_fake_images(2))
    img, img_2 = product.images.all()

    assert product.images.count() == 2
    assert os.path.exists(img.image.path)
    assert os.path.exists(img_2.image.path)

    product.delete_images()

    assert not product.images.count() == 2
    assert not os.path.exists(img.image.path)
    assert not os.path.exists(img_2.image.path) 


def test_update_images(product, product_image):
    """
    Test update of all images. All images are replaced with new ones.
    """
    new_image = create_fake_images(1)

    assert os.path.exists(product_image.image.path)
    assert ProductImage.objects.filter(id=product_image.id).exists()

    product.update_images(new_image)
    
    assert not os.path.exists(product_image.image.path)
    assert not ProductImage.objects.filter(id=product_image.id).exists()
    assert product.images.first().image.name == f"products/pdt_{product.id}/{new_image[0].name}"


def test_product_deletion(product):
    """
    Test deletion of a product instance.
    """

    assert Product.objects.count() == 1
    assert Product.objects.filter(id=product.id).exists()
    
    product.delete()

    assert Product.objects.count() == 0
    assert not Product.objects.filter(id=product.id).exists()


def test_product_deletion_cascades_to_images(product, product_image):
    """
    Test that deletion of a product instance deletes image instances and associated files.
    """
    img_path = product_image.image.path
    product_image_dir = product.get_image_dir()

    assert product.images.count() == 1
    assert ProductImage.objects.count() == 1
    assert os.path.exists(product_image_dir) and os.path.isdir(product_image_dir)
    assert os.path.exists(img_path) and os.path.isfile(img_path)

    product.delete()

    assert ProductImage.objects.count() == 0
    assert not Product.objects.filter(id=product.id).exists()
    assert not os.path.exists(product_image_dir)
    assert not os.path.exists(img_path)
