from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

import uuid


User = get_user_model()


# =============================================================================
# TEST GET ADMIN USERS
# =============================================================================
def test_get_admin_users(client, admin_user, signed_in_superuser):
    """
    Test get all admin users.
    """
    url = reverse('admin-users')
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['code'] == 200
    assert response.data['message'] == "Admin users retrieved successfully."
    assert response.data['data']['count'] == 2
    assert response.data['data']['results']
    assert response.data['data']['previous'] == None
    assert response.data['data']['next'] == None


def test_get_admin_users_by_non_superuser(client, signed_in_admin):
    """
    Test get all admin users by non super user.
    """
    url = reverse('admin-users')
    client.cookies['access_token'] == signed_in_admin['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


# =============================================================================
# TEST GET ADMIN USER WITH ID
# =============================================================================

def test_get_admin_user_by_same_admin_user(client, admin_user, signed_in_admin):
    """
    Test get a specific admin user by same admin user.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    client.cookies['access_token'] == signed_in_admin['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['code'] == 200
    assert response.data['message'] == "Admin user retrieved successfully."
    assert response.data['data']['id'] == str(admin_user.id)


def test_get_admin_user_by_superuser(client, admin_user, signed_in_superuser):
    """
    Test get a specific admin user by super user.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    client.cookies['access_token'] == signed_in_superuser['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['code'] == 200
    assert response.data['message'] == "Admin user retrieved successfully."
    assert response.data['data']['id'] == str(admin_user.id)


def test_get_admin_user_with_invalid_id(client, signed_in_superuser):
    """
    Test get admin user with invalid id.  
    """
    url = reverse('admin-user', kwargs={'user_id': "123-Invalid-id"})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == 400
    assert response.data['message'] == "Invalid admin user id."


def test_get_admin_user_with_non_existent_id(client, signed_in_superuser):
    """
    Test get admin user with non-existent user id.
    """
    url = reverse('admin-user', kwargs={'user_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "Admin user not found."


def test_get_admin_user_by_non_superuser(client, admin_user, signed_in_user):
    """
    Test get a specific admin user by non super user.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    client.cookies['access_token'] == signed_in_user['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


# =============================================================================
# TEST PUT ADMIN USER
# =============================================================================
def test_put_admin_user_by_superuser(client, admin_user, signed_in_superuser):
    """
    Test update a specific admin user by super user.
    Only super user can update staff_id (staff username).
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'staff_id': 'admin-user-updated',
        'old_password': 'Password123#',
        'password': "Password12345#",
        'confirm_password': "Password12345#"
    }
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['code'] == 200
    assert response.data['message'] == "Admin user updated successfully."
    assert response.data['data']['staff_id'] == data['staff_id']


def test_put_admin_user_password_by_same_admin_user(client, admin_user, signed_in_admin):
    """
    Test update admin user password by admin user.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'old_password': 'Password123#',
        'password': "New-password123#",
        'confirm_password': "New-password123#"
    }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['code'] == 200
    assert response.data['message'] == "Admin user updated successfully."

def test_put_admin_user_by_another_user(client, signed_in_admin):
    """
    Test update admin user by a different non superuser admin user.
    """
    admin = User.objects.create_staff(
        staff_id='new-admin-user',
        password='Example123#'
    )
    url = reverse('admin-user', kwargs={'user_id': admin.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
        }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_put_admin_user_staff_id_by_non_superuser(client, admin_user, signed_in_admin):
    """
    Test update a specific admin user staff_id by non super user.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {'staff_id': 'new-admin-user'}
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_put_admin_user_by_non_admin(client, admin_user, signed_in_user):
    """
    Test update admin user by non admin.  
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {'staff_id': 'new-admin-user'}
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_put_admin_user_with_invalid_id(client, signed_in_superuser):
    """
    Test update admin user with invalid id.  
    """
    url = reverse('admin-user', kwargs={'user_id': "123-Invalid-id"})
    data = {'staff_id': 'new-admin-user'}
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == 400
    assert response.data['message'] == "Invalid admin user id."


def test_put_admin_with_non_existent_id(client, signed_in_superuser):
    """
    Test update admin user with non-existent user id.
    """
    url = reverse('admin-user', kwargs={'user_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "Admin user not found."


def test_put_admin_user_password_without_old_password(client, admin_user, signed_in_admin):
    """
    Test update admin user password without old password.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'password': 'Password123#',
        'confirm_password': 'Password123#'
        }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Old password is incorrect."


def test_put_admin_user_password_with_incorrect_old_password(client, admin_user, signed_in_admin):
    """
    Test update admin user password without old password.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'old_password': 'IncorrectOldPassword123#',
        'password': 'Password123#',
        'confirm_password': 'Password123#'
        }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data=data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Old password is incorrect."


def test_put_admin_user_password_mismatch(client, admin_user, signed_in_admin):
    """
    Test update admin user password with mismatching password.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example123#',
        'confirm_password': 'Example1234#',
    }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Password and confirm_password fields do not match."


def test_admin_put_user_password_length(client, admin_user, signed_in_admin):
    """
    Test update user password with a short password.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Exa12#',
        'confirm_password': 'Exa12#',
    }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Admin user update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must be at least 8 characters long."


def test_put_admin_user_password_without_digit(client, admin_user, signed_in_admin):
    """
    Test update admin user with a password without digits.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example#$',
        'confirm_password': 'Example#$',
    }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Admin user update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one digit."


def test_put_admin_user_password_without_special_char(client, admin_user, signed_in_admin):
    """
    Test update admin user with a password without special character.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example123',
        'confirm_password': 'Example123',
    }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Admin user update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one special character."


def test_put_admin_user_password_without_letters(client, admin_user, signed_in_admin):
    """
    Test update admin user with a password without letters.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    data = {
        'old_password': 'Password123#',
        'password': '12345678#',
        'confirm_password': '12345678#',
    }
    client.cookies['access_token'] = signed_in_admin['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Admin user update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one letter."


# =============================================================================
# TEST DELETE ADMIN USER
# =============================================================================

def test_delete_admin_user(client, signed_in_superuser):
    """
    Test delete admin user by superuser.
    """
    admin = User.objects.create_staff(
        staff_id='new-admin',
        password='Password123#'
    )
    url = reverse('admin-user', kwargs={'user_id': admin.id})
    client.cookies['access_token'] == signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    

def test_delete_admin_user_by_non_superuser(client, admin_user, signed_in_admin):
    """
    Test delete admin user by non super user.
    """
    url = reverse('admin-user', kwargs={'user_id': admin_user.id})
    client.cookies['access_token'] == signed_in_admin['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_delete_admin_user_with_invalid_id(client, signed_in_superuser):
    """
    Test delete admin user with invalid user id.
    """
    url = reverse('admin-user', kwargs={'user_id': "123-Invalid-id"})
    client.cookies['access_token'] == signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == 400
    assert response.data['message'] == "Invalid admin user id."


def test_delete_admin_with_non_existent_id(client, signed_in_superuser):
    """
    Test delete admin user with non-existent user id.
    """
    url = reverse('admin-user', kwargs={'user_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "Admin user not found."


def test_delete_super_user_admin_by_self(client, super_user, signed_in_superuser):
    """
    Test delete super user admin by self.
    """
    url = reverse('admin-user', kwargs={'user_id': super_user.id})
    client.cookies['access_token'] = signed_in_superuser['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."
