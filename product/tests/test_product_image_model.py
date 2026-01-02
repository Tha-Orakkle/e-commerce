import os

from product.models import ProductImage


def test_product_image_creation(product, product_image):
    """
    Test the creation of a product image.
    """
    assert product_image.id is not None
    assert type(product_image.id).__name__ == "UUID"
    assert product_image.product == product
    assert ProductImage.objects.count() == 1
    assert product_image.image.name.startswith(f"shp_{product.shop.id}/products/pdt_{product.id}/")
    assert product_image.image.path.startswith(str(product.get_image_dir()))


def test_product_image_relationship(product, product_image):
    """
    Test the relationship between product and product image.
    """
    assert product.images.count() == 1
    assert product.images.first() == product_image


def test_product_image_str(product_image):
    """
    Test the string representation of a product image.
    """
    assert str(product_image) == f"<ProductImage: {product_image.id}> {product_image.image}"


def test_product_image_deletion(product, product_image):
    """
    Tests deletion of a product image instance.
    """
    img_path = product_image.image.path

    assert os.path.exists(img_path)
    assert product.images.count() == 1
    assert product.images.first() == product_image

    product_image.delete()

    assert not os.path.exists(img_path)
    assert product.images.count() == 0
