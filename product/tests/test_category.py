from django.urls import reverse
from rest_framework import status

import pytest
import uuid

from product.models import Category


# =============================================================================
# TEST GET CATGEORIES
# =============================================================================
CATEGORY_URL = reverse('category-list-create')

@pytest.mark.parametrize(
    'user_type', 
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_get_categories(client, category, all_users, user_type):
    """
    Test get all categories.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)

    res = client.get(CATEGORY_URL)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Categories retrieved successfully."
    assert res.data['data']['count'] == 1
    assert 'next' in res.data['data']
    assert 'previous' in res.data['data']
    assert res.data['data']['results'][0]['id'] == str(category.id)
    assert res.data['data']['results'][0]['name'] == category.name
    assert res.data['data']['results'][0]['slug'] == category.slug


def test_get_categories_while_unauthenticated(client, category):
    """
    Test get all categories while unauthenticated.
    (without access token or with invalid token).
    """
    res = client.get(CATEGORY_URL)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.get(CATEGORY_URL)
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# =============================================================================
# TEST GET CATGEORY WITH ID
# =============================================================================

def test_get_category(client, category, customer):
    """
    Test get category by its id.
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})
    client.force_authenticate(user=customer)

    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Category retrieved successfully."
    assert res.data['data']['id'] == str(category.id)
    assert res.data['data']['name'] == category.name

def test_get_category_while_unauthenticated(client, category):
    """
    Test get category by its id while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})

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


def test_get_category_with_invalid_id(client, customer):
    """
    Test get category with invalid id.
    """
    url = reverse('category-detail', kwargs={'category_id': 'invalid_id'})
    client.force_authenticate(user=customer)

    res = client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid category id."


def test_get_category_with_non_existent_id(client, customer):
    """
    Test get category with non-existent id.
    """
    url = reverse('category-detail', kwargs={'category_id': uuid.uuid4()})
    client.force_authenticate(user=customer)

    res = client.get(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No category matching given ID found."


# =============================================================================
# TEST CREATE CATEGORY
# =============================================================================
def test_create_category(client, super_user):
    """
    Test create a new category.
    """
    client.force_authenticate(user=super_user)
    
    data = {"name": "New Category"}
    
    assert Category.objects.count() == 0

    res = client.post(CATEGORY_URL, data, format='json')
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['message'] == "Category created successfully."
    assert res.data['data']['name'] == data['name']
    assert res.data['data']['slug'] == "new-category"
    assert Category.objects.count() == 1


@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_create_category_by_non_super_user(client, all_users, user_type):
    """
    Test create a new category without permission.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)
    
    data = {"name": "New Category"}

    res = client.post(CATEGORY_URL, data, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_create_category_while_unauthenticated(client):
    """
    Test create a new category while unauthenticated.
    (without access token or with invalid token).
    """
    
    data = {"name": "New Category"}

    res = client.post(CATEGORY_URL, data, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.post(CATEGORY_URL, data, format='json')
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"

def test_create_category_with_blank_name(client, super_user):
    """
    Test create a new category with blank name.
    """
    client.force_authenticate(user=super_user)
    
    data = {"name": ""}

    res = client.post(CATEGORY_URL, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['message'] == "Category creation failed."
    assert 'name' in res.data['errors']
    assert res.data['errors']['name'] == ["This field may not be blank."]
    assert Category.objects.count() == 0
    
def test_create_category_with_missing_name(client, super_user):
    """
    Test create a new category with missing name.
    """
    client.force_authenticate(user=super_user)
    
    res = client.post(CATEGORY_URL, {}, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Category creation failed."
    assert 'name' in res.data['errors']
    assert res.data['errors']['name'] == ["This field is required."]
    assert Category.objects.count() == 0


def test_create_category_with_duplicate_name(client, super_user, category):
    """
    Test create a new category with a duplicate name.
    """
    assert Category.objects.count() == 1
    
    client.force_authenticate(user=super_user)
    
    data = {"name": category.name}  # Duplicate name

    res = client.post(CATEGORY_URL, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Category creation failed."
    assert 'name' in res.data['errors']
    assert res.data['errors']['name'] == ["Category with this name already exists."]
    assert Category.objects.count() == 1


def test_create_category_with_invalid_name(client, super_user):
    """
    Test create a new category with an invalid name (too long/too short).
    """
    client.force_authenticate(user=super_user)

    data = {'name': 'a' * 121}  # too long

    res = client.post(CATEGORY_URL, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Category creation failed."
    assert res.data['errors']['name'] == ["Ensure this field has no more than 120 characters."]

    data = {'name': 'a'}  # too short
    res = client.post(CATEGORY_URL, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Category creation failed."
    assert res.data['errors']['name'] == ["Ensure this field has at least 2 characters."]

def test_create_category_with_special_characters(client, super_user):
    """
    Test creating a category with special characters.
    Check that the slug is generated correctly.
    """
    client.force_authenticate(user=super_user)
    
    data = {"name": "Category@123"}  # Name with special characters

    res = client.post(CATEGORY_URL, data, format='json')
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data['message'] == "Category created successfully."
    assert res.data['data']['name'] == data['name']
    assert res.data['data']['slug'] == "category123"


# =============================================================================
# TEST UPDATE CATEGORY
# =============================================================================
def test_update_category(client, category, super_user):
    """
    Test update an existing category.
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})
    client.force_authenticate(user=super_user)

    data = {"name": "Updated Category"}

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['message'] == "Category updated successfully."
    assert res.data['data']['name'] == data['name']
    assert res.data['data']['slug'] == "updated-category"
    category.refresh_from_db()
    assert category.name == data['name']
    assert category.slug == "updated-category"

def test_update_category_while_unauthenticated(client, category):
    """
    Test update an existing category while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})

    data = {"name": "Updated Category"}

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    res = client.patch(url, data, format='json')
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"

def test_update_category_with_blank_name(client, category, super_user):
    """
    Test update an existing category with blank name.
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})
    client.force_authenticate(user=super_user)
    
    data = {"name": ""}

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Category update failed."
    assert 'name' in res.data['errors']
    assert res.data['errors']['name'] == ["This field may not be blank."]
    category.refresh_from_db()
    assert category.name != ""
    assert category.slug != ""


def test_update_category_with_missing_name(client, category, super_user):
    """
    Test update an existing category with missing name.
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})
    client.force_authenticate(user=super_user)
    
    res = client.patch(url, {}, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Category updated successfully."
    category.refresh_from_db()
    assert category.name != ""
    assert category.slug != ""

@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_category_by_non_super_user(client, category, all_users, user_type):
    """
    Test update an existing category without permission.
    """
    user = all_users[user_type]
    url = reverse('category-detail', kwargs={'category_id': category.id})
    client.force_authenticate(user=user)

    data = {"name": "Updated Category"}

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_update_category_with_non_existent_id(client, super_user):
    """
    Test update a category with a non-existent id.
    """
    url = reverse('category-detail', kwargs={'category_id': uuid.uuid4()})
    client.force_authenticate(user=super_user)
    
    data = {"name": "Updated Category"}

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No category matching given ID found."

def test_update_category_with_invalid_id(client, super_user):
    """
    Test update a category with an invalid id.
    """
    url = reverse('category-detail', kwargs={'category_id': 'invalid_id'})
    client.force_authenticate(user=super_user)
    
    data = {"name": "Updated Category"}

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid category id."

def test_update_category_with_duplicate_name(client, category_factory, super_user):
    """
    Test update a category with a duplicate name.
    """
    c1 = category_factory(name="Original Category")
    c2 = category_factory(name="Another Category")

    url = reverse('category-detail', kwargs={'category_id': c2.id})
    client.force_authenticate(user=super_user)


    data = {"name": c1.name}

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Category update failed."
    assert 'name' in res.data['errors']
    assert res.data['errors']['name'] == ["Category with this name already exists."]


def test_update_category_with_invalid_name(client, category, super_user):
    """
    Test update a category with a name that is too long/too short.
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})
    client.force_authenticate(user=super_user)
    
    data = {'name': 'a' * 121}

    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Category update failed."
    assert 'name' in res.data['errors']
    assert res.data['errors']['name'] == ["Ensure this field has no more than 120 characters."]
    
    data = {'name': 'a'}
    res = client.patch(url, data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "Category update failed."
    assert 'name' in res.data['errors']
    assert res.data['errors']['name'] == ["Ensure this field has at least 2 characters."]

# =============================================================================
# TEST DELETE CATEGORY
# =============================================================================
def test_delete_category(client, category, super_user):
    """
    Test delete an existing category.
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})
    client.force_authenticate(user=super_user)
    
    assert Category.objects.count() == 1

    res = client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert Category.objects.count() == 0


def test_delete_category_while_unauthenticated(client, category):
    """
    Test delete an existing category while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('category-detail', kwargs={'category_id': category.id})

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

@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_delete_category_by_non_super_user(client, category, all_users, user_type):
    """
    Test delete an existing category by non super user.
    """
    user = all_users[user_type]
    
    url = reverse('category-detail', kwargs={'category_id': category.id})
    client.force_authenticate(user=user)
    
    res = client.delete(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."


def test_delete_category_with_non_existent_id(client, super_user):
    """
    Test delete a category with a non-existent id.
    """
    url = reverse('category-detail', kwargs={'category_id': uuid.uuid4()})
    client.force_authenticate(user=super_user)

    res = client.delete(url)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No category matching given ID found."


def test_delete_category_with_invalid_id(client, super_user):
    """
    Test delete a category with an invalid id.
    """
    url = reverse('category-detail', kwargs={'category_id': 'invalid_id'})
    client.force_authenticate(user=super_user)

    res = client.delete(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid category id."
