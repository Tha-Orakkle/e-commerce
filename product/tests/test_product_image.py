from django.urls import reverse
from rest_framework import status
from urllib.parse import urlparse

import os
import pytest
import uuid

from .fixtures import create_fake_images, create_large_fake_image, create_fake_files
from product.models import ProductImage


# =============================================================================
# TEST GET PRODUCT IMAGES
# =============================================================================

def test_get_product_images(client, customer, product, product_image_factory):
    """
    Test get all product images.
    """
    for _ in range(3):
        product_image_factory(product=product)

    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Product images retrieved successfully."
    assert len(res.data['data']) == 3
    assert ProductImage.objects.filter(product=product).count() == 3
    img = res.data['data'][0]
    parsed_url = urlparse(img['url'])

    assert img['id'] in [str(pi.id) for pi in ProductImage.objects.filter(product=product)]
    assert parsed_url.path == ProductImage.objects.get(id=img['id']).image.url
    assert parsed_url.netloc

        
def test_get_product_images_with_invalid_product_id(client, customer):
    """
    Test get product images with invalid product id.
    """
    url = reverse('product-image-list-create', kwargs={'product_id': "Invalid_product_id"})
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"        
    assert res.data['code'] == "invalid_uuid"        
    assert res.data['message'] == "Invalid product id."        

def test_get_product_images_with_non_existent_product_id(client, customer):
    """
    Test get product images with non-existent product id.
    """
    url = reverse('product-image-list-create', kwargs={'product_id': uuid.uuid4()})
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"        
    assert res.data['code'] == "not_found"        
    assert res.data['message'] == "No product matching the given ID found."


def test_get_product_images_unauthenticted(client, product):
    """
    Test delete all product images while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST GET PRODUCT IMAGE WITH ID
# =============================================================================

def test_get_product_image(client, customer, product, product_image):
    """
    Test get a specific product image with the product image id.
    """
    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })

    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Product image retrieved successfully."
    assert res.data['data']['id'] == str(product_image.id)
    parsed_url = urlparse(res.data['data']['url'])
    assert parsed_url.path == product_image.image.url
    assert parsed_url.netloc


def test_get_product_image_with_invalid_ids(client, customer,  product, product_image):
    """
    Test get specific product image with invalid product or image id.
    """
    url = reverse('product-image-detail', kwargs={
        'product_id': "Invalid_product_id",
        'image_id': product_image.id
    })
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"        
    assert res.data['code'] == "invalid_uuid"        
    assert res.data['message'] == "Invalid product id."

    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': "Invalid_product_image_id"
    })
    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"        
    assert res.data['code'] == "invalid_uuid"        
    assert res.data['message'] == "Invalid product image id."


def test_get_product_image_with_non_existent_ids(client, customer, product, product_image):
    """
    Test get specific product image with non-existent product or image id.
    """
    url = reverse('product-image-detail', kwargs={
        'product_id': uuid.uuid4(),
        'image_id': product_image.id
    })
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No product matching the given ID found."

    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': uuid.uuid4()
    })
    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"        
    assert res.data['message'] == "No product image matching the given ID found."


def test_get_product_image_unauthenticted(client, product, product_image):
    """
    Test delete a specific product while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"        
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"        
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST DELETE PRODUCT IMAGE
# =============================================================================

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_delete_product_image(client, product, product_image, all_users, user_type):
    """
    Test delete a specific product image by an admin.
    """
    user = all_users[user_type]
    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    assert ProductImage.objects.filter(product=product).count() == 1
    assert os.path.exists(product_image.image.path)
    
    client.force_authenticate(user=user)
    res = client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT

    assert ProductImage.objects.filter(product=product).count() == 0
    assert not os.path.exists(product_image.image.path)


def test_delete_product_image_with_invalid_ids(client, shopowner,  product, product_image):
    """
    Test delete specific product image with invalid product or image id.
    """
    url = reverse('product-image-detail', kwargs={
        'product_id': "Invalid_product_id",
        'image_id': product_image.id
    })
    client.force_authenticate(user=shopowner)
    res = client.delete(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid product id."

    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': "Invalid_product_image_id"
    })
    res = client.delete(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid product image id."


def test_delete_product_image_by_non_existent_ids(client, shopowner, product, product_image):
    """
    Test delete specific product image with non-existent product or image id.
    """
    url = reverse('product-image-detail', kwargs={
        'product_id': uuid.uuid4(),
        'image_id': product_image.id
    })
    client.force_authenticate(user=shopowner)
    res = client.delete(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No product matching the given ID found."

    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': uuid.uuid4()
    })
    res = client.delete(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No product image matching the given ID found."

def test_delete_product_image_unauthenticated(client, product, product_image):
    """
    Test delete a specific product while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


def test_delete_product_image_by_non_staff(client, customer, product, product_image):
    """
    Test delete product image by non-admin.
    """
    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    client.force_authenticate(user=customer)
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_delete_product_image_by_different_shop_staff(client, shopowner_factory, product, product_image):
    """
    Test delete product image by shop staff of a different shop.
    """
    sh = shopowner_factory()
    
    url = reverse('product-image-detail', kwargs={
        'product_id': product.id,
        'image_id': product_image.id
    })
    client.force_authenticate(user=sh)
    res = client.delete(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


# =============================================================================
# TEST POST PRODUCT IMAGE
# =============================================================================
@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_post_product_image(client, product, all_users, user_type):
    """
    Test add a new image to a product instance
    """
    user = all_users[user_type]
    data = {'images': create_fake_images(2)}

    assert product.images.count() == 0
    
    client.force_authenticate(user=user)
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=user)


    res = client.post(url, data, format='multipart')

    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['status'] == "success"
    assert res.data['message'] == "Product images added successfully."
    assert product.images.count() == 2


def test_post_product_image_with_invalid_product_id(client, shopowner):
    """
    Test add new image to a product instance with invalid product id.
    """
    data = {'images': create_fake_images(2)}
    url = reverse('product-image-list-create', kwargs={'product_id': "Invalid_product_id"})

    client.force_authenticate(user=shopowner)
    res = client.post(url, data, format='multipart')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid product id."


def test_post_product_image_with_non_existent_product_id(client, shopowner):
    """
    Test add new image to a product instance with non-existent product id.
    """
    data = {'images': create_fake_images(2)}
    url = reverse('product-image-list-create', kwargs={'product_id': uuid.uuid4()})

    client.force_authenticate(user=shopowner)
    res = client.post(url, data, format='multipart')
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No product matching the given ID found."


def test_post_product_image_unauthenticated(client, product):
    """
    Test add a new image to a product instance while unauthenticated.
    (without access token or with invalid token)
    """
    data = {'images': create_fake_images(2)}
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    res = client.post(url, data, format='multipart')
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.post(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


def test_post_product_image_by_customer(client, customer, product):
    """
    Test add a new image to a product instance by non-admin.
    """
    data = {'images': create_fake_images(2)}
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=customer)
    res = client.post(url, data, format='multipart')
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_post_product_image_by_different_shop_staff(client, shopowner_factory, product):
    """
    Test add a new image to a product instance by shop staff of a different shop.
    """
    sh = shopowner_factory()
    data = {'images': create_fake_images(2)}
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=sh)
    res = client.post(url, data, format='multipart')
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_post_product_image_with_no_images(client, product, shopowner):
    """
    Test create product images endpoint with no images.
    """
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)
    
    res = client.post(url, {}, format='multipart')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Could not add images to product."
    assert res.data['errors']['images'] == ["This list may not be empty."]


def test_post_product_image_with_images_exceeding_8(client, product, shopowner):
    """
    Tets create product images where product already has 8 images.
    """
    product.add_images(create_fake_images(8))
    
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)
    res = client.post(url, {'images': create_fake_images(2)}, format='multipart')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "image_limit_reached"
    assert res.data['message'] == "Product has 8 images. Cannot add more images."
    
    
def test_post_product_image_with_too_many_images(client, product, shopowner):
    """
    Tets create product images where number of images being added exceeds limit.
    """
    product.add_images(create_fake_images(6))
    
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)
    res = client.post(url, {'images': create_fake_images(3)}, format='multipart')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "too_many_images"
    assert res.data['message'] == "Too many images. You can only add 2 more porduct image(s)."
    
def test_post_product_image_with_large_image_size(client, product, shopowner):
    """
    Tets create product images where one or more images exceed size limit.
    """
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)
    large_image = create_large_fake_image(2)

    res = client.post(url, {'images': large_image}, format='multipart')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "image_too_large"
    assert res.data['message'] == "Ensure that all images are less than 2MB"
    
def test_post_product_image_with_invalid_file_type(client, product, shopowner):
    """
    Tets create product images where one or more files are not images.
    """
    url = reverse('product-image-list-create', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)
    fake_files = create_fake_files(2)
    res = client.post(url, {'images': fake_files}, format='multipart')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Could not add images to product."
    img_err = res.data['errors']['images']
    assert len(img_err) == 2
    first_img_err = img_err[0]
    assert "Upload a valid image." in first_img_err[0]
