import os

from product.models import ProductImage


def test_product_image_creation(product, fake_image):
    """
    Test the creation of a product image.
    """
    product_image = ProductImage.objects.create(
        product=product,
        image=fake_image
    )
    assert product_image.id is not None
    assert type(product_image.id).__name__ == "UUID"
    assert product_image.product == product
    assert ProductImage.objects.count() == 1
    assert product_image.image.name == f"products/pdt_{product.id}/test_image.jpg"
    assert product_image.image.path == str(product.get_image_dir()) + "/test_image.jpg"


def test_product_image_relationship(product, fake_image):
    """
    Test the relationship between product and product image.
    """
    product_image = ProductImage.objects.create(
        product=product,
        image=fake_image
    )
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
