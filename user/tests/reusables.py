from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

import uuid

User = get_user_model()

# =============================================================================
# TEST PUT Shop owner
# =============================================================================
def test_put_shopowner_by_superuser(client, shopowner, signed_in_superuser):
    """
    Test update a specific Shop owner by super user.
    Only super user can update staff_handle (staff username).
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'staff_handle': 'shopowner-detail-updated',
        'old_password': 'Password123#',
        'password': "Password12345#",
        'confirm_password': "Password12345#"
    }
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == "Shop owner updated successfully."
    assert response.data['data']['staff_handle'] == data['staff_handle']


def test_put_shopowner_password_by_same_shopowner(client, shopowner, signed_in_shopowner):
    """
    Test update Shop owner password by Shop owner.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'old_password': 'Password123#',
        'password': "New-password123#",
        'confirm_password': "New-password123#"
    }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['message'] == "Shop owner updated successfully."

def test_put_shopowner_by_another_user(client, signed_in_shopowner):
    """
    Test update Shop owner by a different non superuser Shop owner.
    """
    admin = User.objects.create_staff(
        staff_handle='new-shopowner-detail',
        password='Example123#'
    )
    url = reverse('shopowner-detail', kwargs={'shopowner_id': admin.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
        }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_put_shopowner_staff_handle_by_non_superuser(client, shopowner, signed_in_shopowner):
    """
    Test update a specific Shop owner staff_handle by non super user.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {'staff_handle': 'new-shopowner-detail'}
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_put_shopowner_by_non_admin(client, shopowner, signed_in_user):
    """
    Test update Shop owner by non admin.  
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {'staff_handle': 'new-shopowner-detail'}
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_put_shopowner_with_invalid_id(client, signed_in_superuser):
    """
    Test update Shop owner with invalid id.  
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': "123-Invalid-id"})
    data = {'staff_handle': 'new-shopowner-detail'}
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == 400
    assert response.data['message'] == "Invalid Shop owner id."


def test_put_admin_with_non_existent_id(client, signed_in_superuser):
    """
    Test update Shop owner with non-existent user id.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "Shop owner not found."


def test_put_shopowner_password_without_old_password(client, shopowner, signed_in_shopowner):
    """
    Test update Shop owner password without old password.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'password': 'Password123#',
        'confirm_password': 'Password123#'
        }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Old password is incorrect."


def test_put_shopowner_password_with_incorrect_old_password(client, shopowner, signed_in_shopowner):
    """
    Test update Shop owner password without old password.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'old_password': 'IncorrectOldPassword123#',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
        }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Old password is incorrect."


def test_put_shopowner_password_mismatch(client, shopowner, signed_in_shopowner):
    """
    Test update Shop owner password with mismatching password.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example123#',
        'confirm_password': 'Example1234#',
    }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Password and confirm_password fields do not match."


def test_admin_put_user_password_length(client, shopowner, signed_in_shopowner):
    """
    Test update user password with a short password.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Exa12#',
        'confirm_password': 'Exa12#',
    }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Shop owner update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must be at least 8 characters long."


def test_put_shopowner_password_without_digit(client, shopowner, signed_in_shopowner):
    """
    Test update Shop owner with a password without digits.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example#$',
        'confirm_password': 'Example#$',
    }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Shop owner update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one digit."


def test_put_shopowner_password_without_special_char(client, shopowner, signed_in_shopowner):
    """
    Test update Shop owner with a password without special character.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example123',
        'confirm_password': 'Example123',
    }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Shop owner update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one special character."


def test_put_shopowner_password_without_letters(client, shopowner, signed_in_shopowner):
    """
    Test update Shop owner with a password without letters.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    data = {
        'old_password': 'Password123#',
        'password': '12345678#',
        'confirm_password': '12345678#',
    }
    client.cookies['access_token'] = signed_in_shopowner['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Shop owner update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one letter."


# =============================================================================
# TEST DELETE Shop owner
# =============================================================================

def test_delete_shopowner(client, signed_in_superuser):
    """
    Test delete Shop owner by superuser.
    """
    admin = User.objects.create_staff(
        staff_handle='new-admin',
        password='Password123#'
    )
    url = reverse('shopowner-detail', kwargs={'shopowner_id': admin.id})
    client.cookies['access_token'] == signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    

def test_delete_shopowner_by_non_superuser(client, shopowner, signed_in_shopowner):
    """
    Test delete Shop owner by non super user.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': shopowner.id})
    client.cookies['access_token'] == signed_in_shopowner['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_delete_shopowner_with_invalid_id(client, signed_in_superuser):
    """
    Test delete Shop owner with invalid user id.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': "123-Invalid-id"})
    client.cookies['access_token'] == signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == 400
    assert response.data['message'] == "Invalid Shop owner id."


def test_delete_admin_with_non_existent_id(client, signed_in_superuser):
    """
    Test delete Shop owner with non-existent user id.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "Shop owner not found."


def test_delete_super_user_admin_by_self(client, super_user, signed_in_superuser):
    """
    Test delete super user admin by self.
    """
    url = reverse('shopowner-detail', kwargs={'shopowner_id': super_user.id})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."
