from django.urls import reverse
from rest_framework import status
from urllib.parse import urlparse

import os
import uuid

from .conftest import create_fake_images
from product.models import ProductImage


# =============================================================================
# TEST GET PRODUCT IMAGES
# =============================================================================

def test_get_product_images(client, signed_in_user, product, product_image):
    """
    Test get all product images.
    """
    url = reverse('product-images', kwargs={'product_id': product.id})
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == f"Product {product.name} images retrieved."
    parsed_url = urlparse(response.data['data'][0]['url'])
    assert parsed_url.path == product_image.image.url
    assert parsed_url.scheme in ('https', 'http')
    assert parsed_url.netloc


def test_get_product_images_unauthenticted(client, product):
    """
    Test delete all product images while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product-images', kwargs={'product_id': product.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST GET PRODUCT IMAGE WITH ID
# =============================================================================

def test_get_product_image(client, product, signed_in_user, product_image):
    """
    Test get a specific product image with the product image id.
    """
    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })

    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == f"Product {product.name} image retrieved."
    assert response.data['data']['id'] == str(product_image.id)
    parsed_url = urlparse(response.data['data']['url'])
    assert parsed_url.path == product_image.image.url
    assert parsed_url.scheme in ('https', 'http')
    assert parsed_url.netloc


def test_get_product_image_with_invalid_ids(client, signed_in_user,  product, product_image):
    """
    Test get specific product image with invalid product or image id.
    """
    url = reverse('product-image', kwargs={
        'product_id': "Invalid_product_id",
        'image_id': product_image.id
    })
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == f"Invalid product id."

    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': "Invalid_product_image_id"
    })
    response = client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == f"Invalid product image id."


def test_get_product_image_with_non_existent_ids(client, signed_in_admin,  product, product_image):
    """
    Test get specific product image with non-existent product or image id.
    """
    url = reverse('product-image', kwargs={
        'product_id': uuid.uuid4(),
        'image_id': product_image.id
    })
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['message'] == f"Product not found."

    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': uuid.uuid4()
    })
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['message'] == f"Product image not found."

def test_get_product_image_unauthenticted(client, product, product_image):
    """
    Test delete a specific product while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    response = client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST DELETE PRODUCT IMAGE
# =============================================================================

def test_delete_product_image(client, signed_in_admin, product, product_image):
    """
    Test delete a specific product image by an admin.
    """
    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    client.cookies['access_token'] == signed_in_admin['access_token']
    assert ProductImage.objects.count() == 1
    assert os.path.exists(product_image.image.path)
    
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert ProductImage.objects.count() == 0
    assert not os.path.exists(product_image.image.path)


def test_delete_product_image_with_invalid_ids(client, signed_in_admin,  product, product_image):
    """
    Test delete specific product image with invalid product or image id.
    """
    url = reverse('product-image', kwargs={
        'product_id': "Invalid_product_id",
        'image_id': product_image.id
    })
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == f"Invalid product id."

    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': "Invalid_product_image_id"
    })
    response = client.delete(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == f"Invalid product image id."


def test_delete_product_image_by_non_existent_ids(client, signed_in_admin, product, product_image):
    """
    Test delete specific product image with non-existent product or image id.
    """
    url = reverse('product-image', kwargs={
        'product_id': uuid.uuid4(),
        'image_id': product_image.id
    })
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['message'] == f"Product not found."

    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': uuid.uuid4()
    })
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['message'] == f"Product image not found."


def test_delete_product_image_unauthenticted(client, product, product_image):
    """
    Test delete a specific product while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"


def test_delete_product_image_by_non_admin(client, signed_in_user, product, product_image):
    """
    Test delete product image by non-admin.
    """
    url = reverse('product-image', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    client.cookies['access_token'] == signed_in_user['access_token']
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."


# =============================================================================
# TEST POST PRODUCT IMAGE
# =============================================================================
def test_post_product_image(client, signed_in_admin, product):
    """
    Test add a new image to a product instance
    """
    data = {'images': create_fake_images(2)}
    url = reverse('product-images', kwargs={'product_id': product.id})
    client.cookies['access_token'] == signed_in_admin['access_token']

    assert product.images.count() == 0

    response = client.post(url, data, format='multipart')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['message'] == "Product image added successfully."
    assert product.images.count() == 2


def test_post_product_image_with_invalid_product_id(client, signed_in_admin,  product):
    """
    Test add new image to a product instance with invalid product id.
    """
    data = {'images': create_fake_images(2)}
    url = reverse('product-images', kwargs={'product_id': "Invalid_product_id"})

    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.post(url, data, format='multipart')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == f"Invalid product id."


def test_post_product_image_unauthenticted(client, product):
    """
    Test add a new image to a product instance while unauthenticated.
    (without access token or with invalid token)
    """
    data = {'images': create_fake_images(2)}
    url = reverse('product-images', kwargs={'product_id': product.id})
    response = client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.post(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"


def test_post_product_image_by_non_admin(client, signed_in_user, product):
    """
    Test add a new image to a product instance by non-admin.
    """
    data = {'images': create_fake_images(2)}
    url = reverse('product-images', kwargs={'product_id': product.id})
    client.cookies['access_token'] == signed_in_user['access_token']
    response = client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."


def test_post_product_image_with_images_exceeding_8(client, product, signed_in_admin):
    """
    Tets post product images where images already exceed 8.
    """
    product.add_images(create_fake_images(8))
    url = reverse('product-images', kwargs={'product_id': product.id})
    client.cookies['access_token'] == signed_in_admin['access_token']
    
    response = client.post(url, {'images': create_fake_images(2)}, format='multipart')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['message'] == "Product images cannot exceed 8."
