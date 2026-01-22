from django.urls import reverse
from rest_framework import status

import pytest

from product.models import MAX_PRODUCT_CATEGORIES


@pytest.mark.parametrize(
    'user_type',
    ['shopowner', 'shop_staff'],
    ids=['shopowner', 'shop_staff']
)
def test_update_product_category(client, all_users, user_type, product, category_factory):
    """
    Test update product categories.
    """
    user = all_users[user_type]
    url = reverse('product-category-update', kwargs={'product_id': product.id})
    client.force_authenticate(user=user)

    categories = [category_factory() for _ in range(3)]
    
    # Test adding categories
    assert product.categories.count() == 0
    res = client.post(url, data={
        'action': 'add',
        'categories': [c.name for c in categories]
    }, format='json')
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Product categories updated successfully."
    
    product.refresh_from_db()
    assert product.categories.count() == 3
    
    # Test removing categories
    res = client.post(url, data={
        'action': 'remove',
        'categories': [c.name for c in categories]
    }, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Product categories updated successfully."
    
    product.refresh_from_db()
    assert product.categories.count() == 0
    

def test_update_product_categories_when_max_categories_reached(client, shop_staff, product, category_factory):
    """
    Test that adding product to more than categories fails
    when the product reaches maximum categories.
    """
    
    categories = [category_factory() for _ in range(MAX_PRODUCT_CATEGORIES)]
    product.categories.add(*categories)
    
    assert product.categories.count() == MAX_PRODUCT_CATEGORIES
    
    url = reverse('product-category-update', kwargs={'product_id': product.id})
    client.force_authenticate(user=shop_staff)

    res = client.post(url, data={
        'action': 'add',
        'categories': [category_factory().name for _ in range(2)]
    }, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "category_limit_reached"
    assert res.data['message'] == f"Product belongs to {MAX_PRODUCT_CATEGORIES} categories. More categories cannot be added."


def test_update_product_categories_with_too_many_categories(client, shop_staff, product, category_factory):
    """
    Test that adding product to categories fails when too many
    categories are passed.
    """
    categories = [category_factory().name for _ in range(MAX_PRODUCT_CATEGORIES + 1)]
    url = reverse('product-category-update', kwargs={'product_id': product.id})
    client.force_authenticate(user=shop_staff)

    res = client.post(url, data={
        'action': 'add',
        'categories': categories
    }, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "too_many_categories"
    remaining_slot = MAX_PRODUCT_CATEGORIES - product.categories.count()
    assert res.data['message'] == f"Too many categories. You can only add {remaining_slot} new categories."


def test_update_product_categories_with_invalid_action(client, shop_staff, product, category_factory):
    """
    Test updating product categories with the wrong action. 
    """
    assert product.categories.count() == 0
    
    url = reverse('product-category-update', kwargs={'product_id': product.id})
    client.force_authenticate(user=shop_staff)
    res = client.post(url, data={
        'action': 'wrong_action',
        'categories': category_factory().name
    }, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_action"
    assert res.data['message'] == "Enter a valid action: 'add' or 'remove'."
    product.refresh_from_db()
    assert product.categories.count() == 0

    res = client.post(url, data={
        'categories': category_factory().name
    }, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_action"
    assert res.data['message'] == "Enter a valid action: 'add' or 'remove'."
    product.refresh_from_db()
    assert product.categories.count() == 0


def test_update_product_categories_with_missing_categories_field(client, shop_staff, product, category_factory):
    """
    Test that update product categories fails when categories field{s} is/are missing.
    """
    assert product.categories.count() == 0
    
    url = reverse('product-category-update', kwargs={'product_id': product.id})
    client.force_authenticate(user=shop_staff)
    res = client.post(url, data={
        'action': 'add',
    }, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "missing_field"
    assert res.data['message'] == "Please provide a list of categories in the 'categories' field."

    
def test_update_product_with_non_existent_categories(client, shop_staff, product, category_factory):
    """
    Test update product categories with non-existent categories 
    returns a multi-status response.
    """
    assert product.categories.count() == 0
    
    valid_categories = [category_factory().name for _ in range(3)]
    invalid_categories = ['non_existent_1', 'non_existent_2']

    url = reverse('product-category-update', kwargs={'product_id': product.id})
    client.force_authenticate(user=shop_staff)
    res = client.post(url, data={
        'action': 'add',
        'categories': [*valid_categories, *invalid_categories]
    }, format='json')
    
    assert res.status_code == status.HTTP_207_MULTI_STATUS
    assert res.data['status'] == "error"
    assert res.data['code'] == "unprocessed_categories"
    assert res.data['message'] == "Some categories could not be processed."
    assert 'errors' in res.data
    assert 'processed' in res.data['errors']
    assert 'failed' in res.data['errors']
    processed = res.data['errors']['processed']
    failed = res.data['errors']['failed']
    
    from django.utils.text import slugify
    assert all(slugify(c) in processed for c in valid_categories)
    assert all(slugify(c) in failed for c in invalid_categories)


def test_update_product_categories_with_invalid_product_id(client, shop_staff):
    """
    Test update product categories with invalid product id:
        - test for non-existent
        - test for invalid uuid
    """
    
    client.force_authenticate(user=shop_staff)
    
    url = reverse('product-category-update', kwargs={'product_id': 'invalid_uuid'})
    res = client.post(url, data={}, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid product id."
    
    from uuid import uuid4
    
    url = reverse('product-category-update', kwargs={'product_id': uuid4()})
    res = client.post(url, data={}, format='json')
    
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No product matching given ID found."
    
    
def test_update_product_by_unauthenticated_user(client, product):
    """
    Test update product category by unauthenticated user:
        - Test for missing access token
        - test for invalid token
    """
    url = reverse('product-category-update', kwargs={'product_id': product.id})
    
    res = client.post(url, data={}, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = 'invalid_token'
    res = client.post(url, data={}, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


def test_update_product_categories_by_user_without_permission(client, product, shopowner_factory, customer_factory):
    """
    Test update product categories by user without permission:
        - test for customer accessing
        - test for shop owner/staff of another shop
    """
    url = reverse('product-category-update', kwargs={'product_id': product.id})
    
    # test for customer
    cus = customer_factory()
    client.force_authenticate(user=cus)
    res = client.post(url, data={}, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

    # test for owner of another shop
    sh = shopowner_factory()
    client.force_authenticate(user=sh)
    res = client.post(url, data={}, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
