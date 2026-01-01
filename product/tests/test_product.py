from django.urls import reverse
from rest_framework import status 

import os
import pytest
import uuid

from product.models import Product
from .conftest import create_fake_images


# =============================================================================
# TEST GET ALL PRODUCTS
# =============================================================================

PRODUCTS_LIST_URL = reverse('product-list')

def test_get_products(client, shopowner, product_factory, customer):
    """
    Test get all products.
    """
    for _ in range(3):
        product_factory(shop=shopowner.owned_shop)
    
    client.force_authenticate(user=customer)
    
    res = client.get(PRODUCTS_LIST_URL)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Products retrieved successfully."
    assert res.data['data'] is not None
    assert res.data['data']['count'] == 3
    assert 'next' in res.data['data']
    assert 'previous' in res.data['data']
    assert res.data['data']['results'] is not None
    p = res.data['data']['results'][0]
    fields = ['id', 'name', 'description', 'price', 'images', 'categories', 'stock', 'shop']
    assert all(field in p for field in fields)
    assert 'code' not in p['shop']  # ensure shop code is excluded
    assert 'owner' not in p['shop']  # ensure shop owner is excluded


def test_get_products_by_unauthenticated_user(client):
    """
    Test get all products while unauthenticated.
    (without access token or with invalid token).
    """
    res = client.get(PRODUCTS_LIST_URL)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(PRODUCTS_LIST_URL)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST GET ALL PRODUCTS FROM A SHOP
# =============================================================================

def test_get_shop_products(client, shopowner_factory, product_factory, customer):
    """
    Test get all products from a specific shop.
    """
    sh1 = shopowner_factory()
    sh2 = shopowner_factory()

    shop = sh1.owned_shop
    
    for _ in range(3):
        product_factory(shop=shop)
    
    for _ in range(2):
        product_factory(shop=sh2.owned_shop)
        
    client.force_authenticate(user=customer)

    url = reverse('shop-product-list-create', kwargs={'shop_id': shop.id})
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop products retrieved successfully."
    assert res.data['data'] is not None
    Product.objects.count() == 5
    assert res.data['data']['count'] == 3
    assert 'next' in res.data['data']
    assert 'previous' in res.data['data']
    assert res.data['data']['results'] is not None
    p = res.data['data']['results'][0]
    fields = ['id', 'name', 'description', 'price', 'images', 'categories', 'stock', 'shop']
    assert all(field in p for field in fields)
    assert 'code' not in p['shop']  # ensure shop code is excluded
    assert 'owner' not in p['shop']  # ensure shop owner is excluded

def test_get_shop_products_by_unauthenticated_user(client, shopowner, product_factory):
    """
    Test get all products from a specific shop while unauthenticated.
    (without access token or with invalid token).
    """
    shop = shopowner.owned_shop
    
    for _ in range(3):
        product_factory(shop=shop)
        
    url = reverse('shop-product-list-create', kwargs={'shop_id': shop.id})
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

def test_get_shop_products_with_invalid_shop_id(client, customer):
    """
    Test get all products from a specific shop with invalid shop id.
    """
    client.force_authenticate(user=customer)

    url = reverse('shop-product-list-create', kwargs={'shop_id': 'InvalidShopID123'})
    res = client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop id."

def test_get_shop_products_with_non_existent_shop_id(client, customer):
    """
    Test get all products from a specific shop with non-existent shop id.
    """
    client.force_authenticate(user=customer)

    url = reverse('shop-product-list-create', kwargs={'shop_id': uuid.uuid4()})
    res = client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop matching the given ID found."

def test_get_shop_products_with_no_products(client, shopowner, customer):
    """
    Test get all products from a specific shop with no products.
    """
    shop = shopowner.owned_shop
        
    client.force_authenticate(user=customer)

    url = reverse('shop-product-list-create', kwargs={'shop_id': shop.id})
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Shop products retrieved successfully."
    assert res.data['data'] is not None
    assert res.data['data']['count'] == 0
    assert 'next' in res.data['data']
    assert 'previous' in res.data['data']
    assert res.data['data']['results'] == []


# =============================================================================
# TEST GET PRODUCT WITH ID
# =============================================================================

def test_get_product_with_id(client, request, product, product_image, customer):
    """
    Test get specific product with associated id.
    """
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=customer)
    res = client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Product retrieved successfully."
    assert res.data['data']['id'] == str(product.id)
    assert res.data['data']['name'] == product.name
    assert res.data['data']['description'] == product.description
    assert res.data['data']['price'] == f"{product.price:.2f}"
    assert res.data['data']['stock'] == product.stock
    assert 'categories' in res.data['data']
    assert len(res.data['data']['images']) == 1
    res_prod_image = res.data['data']['images'][0]
    assert res_prod_image['id'] == str(product_image.id)
    # assert res_prod_image['url'] == request.build_absolute_uri(product_image.image.url)
    

def test_get_product_with_invalid_id(client, customer):
    """
    Test get specific product with invalid product id.
    """
    url = reverse('product-detail', kwargs={'product_id': 'InvalidID123'})
    client.force_authenticate(user=customer)
    
    res = client.get(url)
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid product id."


def test_get_product_with_non_existent_id(client, customer):
    """
    Test get specific product with non-existent product id.
    """
    url = reverse('product-detail', kwargs={'product_id': uuid.uuid4()})
    client.force_authenticate(user=customer)
    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == f"No product matching the given ID found."


def test_get_product_unauthenticated(client, product):
    """
    Test get specific product while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('product-detail', kwargs={'product_id': product.id})   
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
# TEST DELETE PRODUCT WITH ID
# =============================================================================

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_delete_product_with_id(client, shopowner, product_factory, product_image_factory, all_users, user_type):
    """
    Test delete a specific product with id by shop owner.
    """
    product = product_factory(shop=shopowner.owned_shop)
    product_image = product_image_factory(product=product)

    prod_img_dir = product.get_image_dir()

    assert os.path.exists(prod_img_dir)

    url = reverse('product-detail', kwargs={'product_id': product.id})
    user = all_users[user_type]
    client.force_authenticate(user=user)

    assert Product.objects.count() == 1
    
    res = client.delete(url)

    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert Product.objects.count() == 0
    assert not os.path.exists(product_image.image.path)
    assert not os.path.exists(prod_img_dir)
    

def test_delete_product_with_invalid_id(client, shopowner, product):
    """
    Test delete a specific product with an invalid id.
    """
    url = reverse('product-detail', kwargs={'product_id': 'InvalidID123'})
    client.force_authenticate(user=shopowner)
    
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid product id."

    
def test_delete_product_with_non_existent_id(client, shopowner, product):
    """
    Test delete specific product with non-existent product id.
    """
    url = reverse('product-detail', kwargs={'product_id': uuid.uuid4()})
    client.force_authenticate(user=shopowner)
    res = client.delete(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['message'] == f"No product matching the given ID found."


def test_delete_product_by_non_staff(client, customer, product):
    """
    Test delete specific product by non-staff.
    """
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=customer)
    
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_delete_product_with_non_owned_shop(client, shopowner_factory, product):
    """
    Test delete specific product by shop owner of non-owned shop.
    """
    other_shopowner = shopowner_factory()
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=other_shopowner)
    
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_delete_product_unauthenticated(client, product):
    """
    Test delete a specific product while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product-detail', kwargs={'product_id': product.id})
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


# =============================================================================
# TEST POST NEW PRODUCTS
# =============================================================================

CREATE_PRODUCT_DATA = {
    'name': 'Micro wave',
    'description': 'A micro wave oven',
    'price': 20.00,
}


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_post_product(client, temp_media_root, shopowner, all_users, user_type):
    """
    Test create a new product.
    """
    data = CREATE_PRODUCT_DATA.copy()
    user = all_users[user_type]
    assert Product.objects.count() == 0
    
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    client.force_authenticate(user=user)
    res = client.post(url, data, format='json')
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['status'] == "success"
    assert res.data['message'] == "Product created successfully."
    assert res.data['data'] is not None
    assert res.data['data']['id'] is not None
    assert res.data['data']['name'] == data['name']
    assert res.data['data']['description'] == data['description']
    assert res.data['data']['price'] == f"{data['price']:.2f}"
    assert res.data['data']['stock'] == 0
    assert res.data['data']['created_at'] is not None
    assert res.data['data']['updated_at'] is not None
    assert res.data['data']['deactivated_at'] is None
    
    shop_res = res.data['data']['shop']
    assert shop_res['id'] == str(shopowner.owned_shop.id)
    assert shop_res['name'] == shopowner.owned_shop.name
    assert shop_res['description'] == shopowner.owned_shop.description

    p_id = res.data['data']['id']

    Product.objects.count() == 1
    product = Product.objects.filter(id=p_id).first()
    assert product is not None
    assert product.name == data['name']
    assert product.description == data['description']
    assert product.price == data['price']
    assert product.images.count() == 0


def test_post_product_with_negative_price(client, temp_media_root, shopowner):
    """
    Test create a new product with a negative price.
    Negative numbers will resolve to 0.00
    """
    data = CREATE_PRODUCT_DATA.copy()
    data['price'] = -50.00
    assert Product.objects.count() == 0

    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    client.force_authenticate(user=shopowner)
    res = client.post(url, data, format='json')
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['message'] == "Product created successfully."
    assert res.data['data']['price'] == "0.00"

def test_post_product_with_price_longer_than_ten_digits(client, temp_media_root, shopowner):
    """
    Test create a new product with a price longer than 10 digits.
    """
    data = CREATE_PRODUCT_DATA.copy()
    data['price'] = 12345678901.99
    assert Product.objects.count() == 0

    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    client.force_authenticate(user=shopowner)
    res = client.post(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product creation failed."
    assert res.data['errors']['price'][0] == "Ensure that there are no more than 10 digits in total."

    data['price'] = 1234567890.9978  # 11 digits before decimal point
    res = client.post(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product creation failed."
    assert res.data['errors']['price'][0] == "Ensure that there are no more than 10 digits in total."


def test_post_product_with_price_with_more_than_eight_digits_before_decimal(client, temp_media_root, shopowner):
    """
    Test create a new product with a price with more than 8 digits before decimal point.
    """
    data = CREATE_PRODUCT_DATA.copy()
    data['price'] = 123456789.9  # 9 digits before decimal point
    assert Product.objects.count() == 0

    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    client.force_authenticate(user=shopowner)
    res = client.post(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product creation failed."
    assert res.data['errors']['price'][0] == "Ensure that there are no more than 8 digits before the decimal point."


def test_post_product_with_duplicate_name_in_a_shop(client, shopowner, product_factory):
    """
    Test create a new product with a name that already exists in the shop.
    """
    existing_product = product_factory(shop=shopowner.owned_shop, name="Unique Product")
    data = CREATE_PRODUCT_DATA.copy()
    data['name'] = existing_product.name  # duplicate name

    assert Product.objects.count() == 1
    
    client.force_authenticate(user=shopowner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product creation failed."
    assert res.data['errors']['name'][0] == "A product with this name already exists in the shop."
    assert Product.objects.count() == 1
    
def test_post_product_with_duplicate_name_in_different_shops(client, shopowner_factory, product_factory):
    """
    Test create a new product with a name that already exists in a different shop.
    """
    shop1 = shopowner_factory().owned_shop
    shop2 = shopowner_factory().owned_shop

    existing_product = product_factory(shop=shop1, name="Common Product")
    data = CREATE_PRODUCT_DATA.copy()
    data['name'] = existing_product.name  # duplicate name in different shop

    assert Product.objects.count() == 1
    
    client.force_authenticate(user=shop2.owner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': shop2.id})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['status'] == "success"
    assert res.data['message'] == "Product created successfully."
    assert Product.objects.count() == 2


def test_post_product_with_only_name(client, shopowner):
    """
    Test create a new product without other data but the product name.
    """
    data = {'name': 'Test Micro wave'}

    assert Product.objects.count() == 0
    
    client.force_authenticate(user=shopowner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['status'] == "success"
    assert res.data['message'] == "Product created successfully."
    assert res.data['data']['name'] == data['name']
    assert res.data['data']['description'] == ""
    assert res.data['data']['price'] == "0.00"
    assert Product.objects.count() == 1

    id = res.data['data']['id']

    product = Product.objects.filter(id=id).first()
    assert product.images.count() == 0
    

def test_post_product_with_missing_name(client, temp_media_root, shopowner):
    """
    Test create a product with missing name field.
    """
    data = CREATE_PRODUCT_DATA.copy()
    del data['name']
    client.force_authenticate(user=shopowner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})

    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product creation failed."
    assert res.data['errors']['name'][0] == "This field is required."


def test_post_product_with_blank_name_field(client, temp_media_root, shopowner):
    """
    Test create a product with a blank name field.
    """
    data = CREATE_PRODUCT_DATA.copy()
    data['name'] = ''
    client.force_authenticate(user=shopowner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product creation failed."
    assert res.data['errors']['name'][0] == "This field may not be blank."


def test_post_product_with_invalid_name(client, temp_media_root, shopowner):
    """
    Test create a product with a name that is too long.
    """    
    data = CREATE_PRODUCT_DATA.copy()
    data['name'] = "A" * 51  # Name too long

    client.force_authenticate(user=shopowner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product creation failed."
    assert res.data['errors']['name'][0] == "Ensure this field has no more than 50 characters."


def test_post_product_with_invalid_shop_id(client, temp_media_root, shopowner):
    """
    Test create a product with an invalid shop id.
    """
    data = CREATE_PRODUCT_DATA.copy()
    client.force_authenticate(user=shopowner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': 'InvalidShopID123'})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop id."
    
def test_post_product_with_non_existent_shop_id(client, temp_media_root, shopowner):
    """
    Test create a product with a non-existent shop id.
    """
    data = CREATE_PRODUCT_DATA.copy()
    client.force_authenticate(user=shopowner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': uuid.uuid4()})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop matching the given ID found."
    

def test_post_product_by_different_shop_owner(client, shopowner_factory):
    """
    Test create a product by a different shop owner.
    """
    other_shopowner = shopowner_factory()
    data = CREATE_PRODUCT_DATA.copy()
    client.force_authenticate(user=other_shopowner)
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner_factory().owned_shop.id})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_post_product_by_customer(client, customer, shopowner):
    """
    Test create a product by non-admin user.
    """
    data = CREATE_PRODUCT_DATA.copy()
    client.force_authenticate(user=customer)
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
    
    
def test_post_product_unauthenticated(client, shopowner):
    """
    Test create a product while unauthenticated.
    (without access token or with invalid token).
    """
    data = CREATE_PRODUCT_DATA.copy()
    url = reverse('shop-product-list-create', kwargs={'shop_id': shopowner.owned_shop.id})
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.post(url, data, format='json')

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST PUT UPDATE PRODUCT
# =============================================================================

@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_patch_product(client, product, all_users, user_type):
    """
    Test update a product instance.
    """
    user=all_users[user_type]
    data = CREATE_PRODUCT_DATA.copy()
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=user)

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Product updated successfully."
    
    assert res.data['data']['name'] == data['name']
    assert res.data['data']['description'] == data['description']
    assert res.data['data']['price'] == f"{data['price']:.2f}"
    
    new_product_inst = Product.objects.filter(id=product.id).first()

    assert new_product_inst.name == data['name']
    assert new_product_inst.price == data['price']
    assert new_product_inst.description == data['description']

def test_patch_products_with_negative_price(client, product, shopowner):
    """
    Test update a product with a negative price.
    Negative numbers will resolve to 0.00
    """
    data = {'price': -9.99}
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Product updated successfully."
    assert res.data['data']['price'] == "0.00"

def test_patch_product_with_price_longer_than_ten_digits(client, product, shopowner):
    """
    Test update a product with a price longer than 10 digits.
    """
    data = {'price': 12345678901.99}
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product update failed."
    assert res.data['errors']['price'][0] == "Ensure that there are no more than 10 digits in total."

    data['price'] = 1234567.9978
    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product update failed."
    assert res.data['errors']['price'][0] == "Ensure that there are no more than 10 digits in total."

def test_patch_product_with_price_with_more_than_eight_digits_before_decimal(client, product, shopowner):
    """
    Test update a product with a price with more than 8 digits before decimal point.
    """
    data = {'price': 123456789.9}  # 9 digits before decimal point
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product update failed."
    assert res.data['errors']['price'][0] == "Ensure that there are no more than 8 digits before the decimal point."

def test_patch_product_with_duplicate_name_in_a_shop(client, product_factory, shopowner):
    """
    Test update a product with a name that already exists in the shop.
    """
    existing_product = product_factory(shop=shopowner.owned_shop, name="Existing Product")
    product = product_factory(shop=shopowner.owned_shop, name="Original Product")

    data = {'name': existing_product.name}  # duplicate name
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Product update failed."
    assert res.data['errors']['name'][0] == "A product with this name already exists in the shop."

def test_patch_product_by_customer(client, product, customer):
    """
    Test update  a product instance by customer.
    """
    data = CREATE_PRODUCT_DATA.copy()
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=customer)

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_patch_product_by_non_owned_shop(client, shopowner_factory, product):
    """
    Test update  a product instance by shop owner of non-owned shop.
    """
    other_shopowner = shopowner_factory()
    data = CREATE_PRODUCT_DATA.copy()
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=other_shopowner)

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_patch_product_with_invalid_product_id(client, shopowner,  product):
    """
    Test update specific product with invalid product id.
    """
    url = reverse('product-detail', kwargs={'product_id': "Invalid_product_id"})

    client.force_authenticate(user=shopowner)
    res = client.patch(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid product id."


def test_patch_product_with_non_existent_product_id(client, shopowner, product):
    """
    Test update specific product with non-existent product id.
    """
    url = reverse('product-detail', kwargs={'product_id': uuid.uuid4()})
    client.force_authenticate(user=shopowner)
    res = client.patch(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No product matching the given ID found."


def test_patch_product_unaunthenticted(client, product):
    """
    Test delete a specific product while unauthenticated.
    (without access token or with invalid token)
    """
    url = reverse('product-detail', kwargs={'product_id': product.id})
    res = client.patch(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.delete(url)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['message'] == "Token is invalid or expired"
    
def test_patch_product_with_read_only_fields(client, product, shopowner):
    """
    Test update a product instance with read-only fields.
    """
    data = {
        'id': str(uuid.uuid4()),
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-01-01T00:00:00Z',
        'deactivated_at': '2023-01-01T00:00:00Z',
    }
    url = reverse('product-detail', kwargs={'product_id': product.id})
    client.force_authenticate(user=shopowner)

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Product updated successfully."
    
    assert res.data['data']['id'] == str(product.id)
    assert res.data['data']['created_at'] != '2023-01-01T00:00:00Z'
    assert res.data['data']['updated_at'] != '2023-01-01T00:00:00Z'
    assert res.data['data']['deactivated_at'] is None
    
    new_product_inst = Product.objects.filter(id=product.id).first()

    assert new_product_inst.id == product.id
    assert new_product_inst.created_at != '2023-01-01T00:00:00Z'
    assert new_product_inst.updated_at != '2023-01-01T00:00:00Z'
    assert new_product_inst.deactivated_at is None
