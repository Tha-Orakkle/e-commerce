from django.urls import reverse
from rest_framework import status 

from product.models import Product
from .conftest import create_fake_images

# =============================================================================
# TEST GET PRODUCTS
# =============================================================================

products_url = reverse('products')

def test_get_products(client, signed_in_user, product):
    """
    Test get all products.
    """
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.get(products_url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == "Products retrieved successfully."
    assert response.data['data'] is not None
    assert response.data['data']['count'] == 1
    assert response.data['data']['results'][0]['id'] == str(product.id)


def test_get_products_unauthenticated(client):
    """
    Test get all products while unauthenticated.
    (without access token or with invalid token).
    """
    response = client.get(products_url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.get(products_url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"



# =============================================================================
# TEST GET PRODUCT WITH ID
# =============================================================================

def test_get_product_with_id(client, product, signed_in_user):
    """
    Test get specific product with associated id.
    """
    url = reverse('product', kwargs={'product_id': product.id})
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == "Product retrieved successfully."
    assert response.data['data']['id'] == str(product.id)
    assert response.data['data']['name'] == product.name


def test_get_product_with_invalid_id(client, signed_in_user):
    """
    Test get specific product with invalid product id.
    """
    url = reverse('product', kwargs={'product_id': 'InvalidID123'})
    client.cookies['access_token'] = signed_in_user['access_token']
    
    response = client.get(url)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid product id."



def test_get_product_unaunthenticated(client, product):
    """
    Test get specific product while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('product', kwargs={'product_id': product.id})   
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
# TEST DELETE PRODUCT WITH ID
# =============================================================================

def test_delete_product_with_id(client, signed_in_admin, product):
    """
    Test delete a specific product with id by admin user.
    """
    url = reverse('product', kwargs={'product_id': product.id})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    assert Product.objects.count() == 1
    
    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Product.objects.count() == 0 


def test_delete_product_with_invalid_id(client, signed_in_admin, product):
    """
    Test delete a specific product with an invalid id.
    """
    url = reverse('product', kwargs={'product_id': 'InvalidID123'})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid product id."


def test_delete_product_by_non_admin_user(client, signed_in_user, product):
    """
    Test delete specific product by non-admin user.
    """
    url = reverse('product', kwargs={'product_id': product.id})
    client.cookies['access_token'] = signed_in_user['access_token']
    
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."


def test_delete_product_unauthenticated(client, product):
    """
    Test delete a specific product while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product', kwargs={'product_id': product.id})
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"



# =============================================================================
# TEST POST NEW PRODUCTS
# =============================================================================

def test_post_products(client, temp_media_root, signed_in_admin):
    """
    Test create a new product.
    """
    data = {
        'name': 'Test Micro wave',
        'description': 'A micro wave oven',
        'price': 120000.00,
        'images': create_fake_images(4)
    }
    assert Product.objects.count() == 0
    client.cookies['access_token'] == signed_in_admin['access_token']
    response = client.post(products_url, data, format='multipart')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['status'] == "success"
    assert response.data['message'] == "Product created successfully."
    assert response.data['data']['name'] == data['name']
    assert response.data['data']['description'] == data['description']
    assert response.data['data']['price'] == f"{data['price']:.2f}"

    id = response.data['data']['id']

    Product.objects.count() == 1
    product = Product.objects.filter(id=id).first()
    assert product is not None
    assert product.name == data['name']
    assert product.description == data['description']
    assert product.price == data['price']
    assert product.images.count() == 4 # we created just 4 fake images

def test_post_product_with_more_than_8_images(client, temp_media_root, signed_in_admin):
    """
    Test create a new product with more than 8 images.
    NB: products can not have more than 8 images.
    """
    client.cookies['access_token'] == signed_in_admin['access_token']
    data = {
        'name': 'New Product',
        'description': 'New Product Description',
        'price': 120000.00,
        'images': create_fake_images(12) 
    }
    response = client.post(products_url, data, format='multipart')
    assert response.status_code == status.HTTP_201_CREATED
    product = Product.objects.first()
    
    assert product.images.count() == 8 # only 8 images will be saved



def test_post_products_with_only_name(client, temp_media_root, signed_in_admin):
    """
    Test create a new product without other data but the product name.
    """
    data = {'name': 'Test Micro wave'}
    assert Product.objects.count() == 0
    client.cookies['access_token'] == signed_in_admin['access_token']
    response = client.post(products_url, data, format='multipart')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['status'] == "success"
    assert response.data['data']['name'] == data['name']
    assert response.data['data']['description'] == ""
    assert response.data['data']['price'] == "0.00"
    assert Product.objects.count() == 1

    id = response.data['data']['id']

    product = Product.objects.filter(id=id).first()
    assert product.images.count() == 0
    

def test_post_product_with_missing_name(client, temp_media_root, signed_in_admin):
    """
    Test create a product with missing name field.
    """
    data = {
        'description': 'A micro wave oven',
        'price': 120000.00,
        'images': create_fake_images(1)
    }
    client.cookies['access_token'] == signed_in_admin['access_token']
    response = client.post(products_url, data, format='multipart')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Product creation failed."
    assert response.data['errors']['name'][0] == "This field is required."


def test_post_product_with_blank_name_field(client, temp_media_root, signed_in_admin):
    """
    Test create a product with a blank name field.
    """
    data = {
        'name': '',
        'description': 'A micro wave oven',
        'price': 120000.00,
        'images': create_fake_images(1)
    }
    client.cookies['access_token'] == signed_in_admin['access_token']
    response = client.post(products_url, data, format='multipart')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Product creation failed."
    assert response.data['errors']['name'][0] == "This field may not be blank."



def test_post_product_by_non_admin(client, temp_media_root, signed_in_user):
    """
    Test create a product by non-admin user.
    """
    data = {
        'name': 'Test Micro wave',
        'description': 'A micro wave oven',
        'price': 120000.00
    }
    client.cookies['access_token'] == signed_in_user['access_token']
    response = client.post(products_url, data, format='multipart')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."
    


# =============================================================================
# TEST PUT UPDATE PRODUCT
# =============================================================================

def test_put_product(client, product, product_image, signed_in_admin):
    """
    Test update a product instance.
    """
    data = {
        'name': 'OX fan',
        'description': 'An OX standing fan',
        'price': 20.00,
        'images': create_fake_images(2)
    }
    url = reverse('product', kwargs={'product_id': product.id})
    client.cookies['access_token'] = signed_in_admin['access_token']

    response = client.put(url, data, format='multipart')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == "Product updated successfully."
    new_product_inst = Product.objects.filter(id=product.id).first()

    assert new_product_inst.name == data['name']
    assert new_product_inst.price == data['price']
    assert new_product_inst.description == data['description']

    # check old image is no longer associated with product
    assert product_image.id not in new_product_inst.images.values_list('id', flat=True) 
    assert new_product_inst.images.count() == 2


def test_put_product_with_more_than_8_images(client, product, signed_in_admin):
    """
    Test update product with more than 8 images.
    NB: products can not have more than 8 images.
    """
    url = reverse('product', kwargs={'product_id': product.id})
    data = {'images': create_fake_images(12)}
    client.cookies['access_token'] == signed_in_admin['access_token']
    response = client.put(url, data, format='multipart')

    assert response.status_code == status.HTTP_200_OK
    product = Product.objects.filter(id=product.id).first()
    
    assert product.images.count() == 8 # only 8 images will be saved



def test_put_product_by_non_admin(client, product, signed_in_user):
    """
    Test update  a product instance by a non-admin.
    """
    data = {
        'name': 'OX fan',
        'description:': 'An OX standing fan',
        'price': 20.00
    }
    url = reverse('product', kwargs={'product_id': product.id})
    client.cookies['access_token'] = signed_in_user['access_token']

    response = client.put(url, data, format='multipart')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."


def test_put_product_unaunthenticted(client, product):
    """
    Test delete a specific product while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product', kwargs={'product_id': product.id})
    response = client.put(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"
