from django.urls import reverse
from rest_framework import status

import uuid

from product.models import Category


# =============================================================================
# TEST GET CATGEORIES
# =============================================================================
category_url = reverse('categories')

def test_get_categories(client, category, signed_in_user):
    """
    Test get all categories.
    """
    client.cookies['access_token'] == signed_in_user['access_token']

    response = client.get(category_url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == "Categories retrieved successfully."
    assert response.data['data']['count'] == 1
    assert response.data['data']['results'][0]['id'] == str(category.id)
    assert response.data['data']['results'][0]['name'] == category.name


def test_get_categories_while_unauthenticated(client, category):
    """
    Test get all categories while unauthenticated.
    (without access token or with invalid token).
    """
    response = client.get(category_url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.get(category_url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"



# =============================================================================
# TEST GET CATGEORY WITH ID
# =============================================================================

def test_get_category(client, category, signed_in_user):
    """
    Test get category by its id.
    """
    url = reverse('category', kwargs={'category_id': category.id})
    client.cookies['access_token'] = signed_in_user['access_token']

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == "Category retrieved successfully."
    assert response.data['data']['id'] == str(category.id)
    assert response.data['data']['name'] == category.name

def test_get_category_while_unauthenticated(client, category):
    """
    Test get category by its id while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('category', kwargs={'category_id': category.id})

    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"


def test_get_category_with_invalid_id(client, signed_in_user):
    """
    Test get category with invalid id.
    """
    url = reverse('category', kwargs={'category_id': 'invalid_id'})
    client.cookies['access_token'] = signed_in_user['access_token']

    response = client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid category id."


def test_get_category_with_non_existent_id(client, signed_in_user):
    """
    Test get category with non-existent id.
    """
    url = reverse('category', kwargs={'category_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_user['access_token']

    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category not found."


# =============================================================================
# TEST CREATE CATEGORY
# =============================================================================
def test_create_category(client, signed_in_admin):
    """
    Test create a new category.
    """
    url = reverse('categories')
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": "New Category"}
    
    assert Category.objects.count() == 0

    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['message'] == "Category created successfully."
    assert response.data['data']['name'] == data['name']
    assert response.data['data']['slug'] == "new-category"
    assert Category.objects.count() == 1

def test_create_category_while_unauthenticated(client):
    """
    Test create a new category while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('categories')
    
    data = {"name": "New Category"}

    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.post(url, data, format='json')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"

def test_create_category_with_invalid_data(client, signed_in_admin):
    """
    Test create a new category with invalid data.
    """
    url = reverse('categories')
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": ""}  # Invalid name

    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category creation failed."
    assert 'name' in response.data['errors']

def test_create_category_without_permission(client, signed_in_user):
    """
    Test create a new category without permission.
    """
    url = reverse('categories')
    client.cookies['access_token'] = signed_in_user['access_token']
    
    data = {"name": "New Category"}

    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."

def test_create_category_with_duplicate_name(client, signed_in_admin, category):
    """
    Test create a new category with a duplicate name.
    """
    url = reverse('categories')
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": category.name}  # Duplicate name

    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category creation failed."
    assert 'name' in response.data['errors']

def test_create_category_with_long_name(client, signed_in_admin):
    """
    Test create a new category with a name that is too long.
    """
    url = reverse('categories')
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": "a" * 256}  # Name longer than allowed

    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category creation failed."
    assert 'name' in response.data['errors']

def test_create_category_with_special_characters(client, signed_in_admin):
    """
    Test create a new category with a name that contains special characters.
    """
    url = reverse('categories')
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": "Category@123"}  # Name with special characters

    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['message'] == "Category created successfully."
    assert response.data['data']['name'] == data['name']
    assert response.data['data']['slug'] == "category123"


# =============================================================================
# TEST UPDATE CATEGORY
# =============================================================================
def test_update_category(client, category, signed_in_admin):
    """
    Test update an existing category.
    """
    url = reverse('category', kwargs={'category_id': category.id})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": "Updated Category"}

    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == "Category updated successfully."
    assert response.data['data']['name'] == data['name']
    assert response.data['data']['slug'] == "updated-category"
    category.refresh_from_db()
    assert category.name == data['name']

def test_update_category_while_unauthenticated(client, category):
    """
    Test update an existing category while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('category', kwargs={'category_id': category.id})

    data = {"name": "Updated Category"}

    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.put(url, data, format='json')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"

def test_update_category_with_invalid_data(client, category, signed_in_admin):
    """
    Test update an existing category with invalid data.
    """
    url = reverse('category', kwargs={'category_id': category.id})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": ""}  # Invalid name

    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category update failed."
    assert 'name' in response.data['errors']

def test_update_category_without_permission(client, category, signed_in_user):
    """
    Test update an existing category without permission.
    """
    url = reverse('category', kwargs={'category_id': category.id})
    client.cookies['access_token'] = signed_in_user['access_token']
    
    data = {"name": "Updated Category"}

    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."

def test_update_category_with_non_existent_id(client, signed_in_admin):
    """
    Test update a category with a non-existent id.
    """
    url = reverse('category', kwargs={'category_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": "Updated Category"}

    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category not found."

def test_update_category_with_invalid_id(client, signed_in_admin):
    """
    Test update a category with an invalid id.
    """
    url = reverse('category', kwargs={'category_id': 'invalid_id'})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": "Updated Category"}

    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid category id."

def test_update_category_with_duplicate_name(client, category, signed_in_admin):
    """
    Test update a category with a duplicate name.
    """
    url = reverse('category', kwargs={'category_id': category.id})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    # Create another category with the same name
    duplicate_category = Category.objects.create(name="Duplicate Category")
    
    data = {"name": duplicate_category.name}  # Duplicate name

    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category update failed."
    assert 'name' in response.data['errors']

def test_update_category_with_long_name(client, category, signed_in_admin):
    """
    Test update a category with a name that is too long.
    """
    url = reverse('category', kwargs={'category_id': category.id})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    data = {"name": "a" * 256}  # Name longer than allowed

    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category update failed."
    assert 'name' in response.data['errors']

# =============================================================================
# TEST DELETE CATEGORY
# =============================================================================
def test_delete_category(client, category, signed_in_admin):
    """
    Test delete an existing category.
    """
    url = reverse('category', kwargs={'category_id': category.id})
    client.cookies['access_token'] = signed_in_admin['access_token']
    
    assert Category.objects.count() == 1

    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Category.objects.count() == 0


def test_delete_category_while_unauthenticated(client, category):
    """
    Test delete an existing category while unauthenticated.
    (without access token or with invalid token).
    """
    url = reverse('category', kwargs={'category_id': category.id})

    response = client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."

    client.cookies['access_token'] = "Invalid_access_token2445"
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['status'] == "error"
    assert response.data['message'] == "Token is invalid or expired"


def test_delete_category_without_permission(client, category, signed_in_user):
    """
    Test delete an existing category without permission.
    """
    url = reverse('category', kwargs={'category_id': category.id})
    client.cookies['access_token'] = signed_in_user['access_token']
    
    response = client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."

def test_delete_category_with_non_existent_id(client, signed_in_admin):
    """
    Test delete a category with a non-existent id.
    """
    url = reverse('category', kwargs={'category_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_admin['access_token']

    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['message'] == "Category not found."


def test_delete_category_with_invalid_id(client, signed_in_admin):
    """
    Test delete a category with an invalid id.
    """
    url = reverse('category', kwargs={'category_id': 'invalid_id'})
    client.cookies['access_token'] = signed_in_admin['access_token']

    response = client.delete(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['message'] == "Invalid category id."
