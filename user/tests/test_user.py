"""
Test module for the user enpoints
"""
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

import uuid

User = get_user_model()


# =============================================================================
# TEST GET USERS
# =============================================================================
def test_get_users(client, user, signed_in_user):
    """
    Test get all users by admin.
    """
    tokens = signed_in_user
    url = reverse('users')
    client.cookies['access_token'] == tokens['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['code'] == 200
    assert response.data['message'] == "Users retrieved successfully."
    assert response.data['data']['count'] == 1



# =============================================================================
# TEST GET USERS WITH ID
# =============================================================================

def test_get_user_with_id(client, user, signed_in_user):
    """
    Test get user with the user's id.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == "success"
    assert response.data['code'] == 200
    assert response.data['message'] == "User retrieved successfully."
    assert response.data['data']
    assert response.data['data']['id'] == str(user.id)

    
def test_get_user_with_invalid_id(client, signed_in_user):
    """
    Test get user with invalid id.
    """
    url = reverse('user', kwargs={'user_id': "45678909876543"})
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == 400
    assert response.data['message'] == "Invalid user id."


def test_get_user_with_non_existent_id(client, signed_in_user):
    """
    Test get user with non-existent id.
    """
    url = reverse('user', kwargs={'user_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "User not found."


# =============================================================================
# TEST PUT USER
# =============================================================================

def test_put_user_email(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user email address to a new one.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    tokens = signed_in_user
    data = {'email': 'new_email@email.com'}
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_called_once()
    assert response.status_code == status.HTTP_200_OK
    assert response.data['code'] == 200
    assert response.data['status'] == "success"
    assert response.data['message'] == "User updated successfully."
    assert response.data['data']
    assert response.data['data']['id'] == str(user.id)
    assert response.data['data']['email'] == data['email']
    assert response.data['data']['is_verified'] == False


def test_put_user_email_with_same_verified_email(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user email address with the same verified email address.
    """
    user.is_verified = True
    user.save()
    url = reverse('user', kwargs={'user_id': user.id})
    data = {
        'email': user.email,
        'passord': 'Password1234#',
        'confirm_passord': 'Password1234#'
    }
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_200_OK
    assert response.data['code'] == 200
    assert response.data['status'] == "success"
    assert response.data['message'] == "User updated successfully."
    assert response.data['data']['is_verified'] == True


def test_put_user_with_invalid_id(client, signed_in_user):
    """
    Test update user with invalid id.  
    """
    url = reverse('user', kwargs={'user_id': "123-Invalid-id"})
    data = {
        'passord': 'Password1234#',
        'confirm_passord': 'Password1234#'
    }
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == 400
    assert response.data['message'] == "Invalid user id."


def test_put_user_with_non_existent_id(client, signed_in_user):
    """
    Test update user with non-existent id.
    """
    url = reverse('user', kwargs={'user_id': uuid.uuid4()})
    data = {
        'passord': 'Password1234#',
        'confirm_passord': 'Password1234#'
    }
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.put(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "User not found."



def test_put_user_email_invalid_email(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user email address with an invalid email address.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    tokens = signed_in_user
    data = {
        'email': 'invalid_email'
    }
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User update failed."
    assert response.data['errors']['email']
    assert response.data['errors']['email'][0] == "Enter a valid email address."


def test_put_user_email_existing_email(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user email address with an existing emaill address.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    User.objects.create_user(
        email="user2@email.com",
        password="Password123#"
    )
    data = {
        'email': 'user2@email.com'
    }
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User update failed."
    assert response.data['errors']['email']
    assert response.data['errors']['email'][0] == "user with this email already exists."


def test_put_user_password(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user password.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    tokens = signed_in_user
    data = {
        'old_password': 'Password123#',
        'password': 'Example123#',
        'confirm_password': 'Example123#'
    }
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_200_OK
    assert response.data['code'] == 200
    assert response.data['status'] == "success"
    assert response.data['message'] == "User updated successfully."
    assert response.data['data']
    assert response.data['data']['id'] == str(user.id)


def test_put_user_password_without_old_password(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user password without old password.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    tokens = signed_in_user
    data = {
        'password': 'Example123#',
        'confirm_password': 'Example123#'
    }
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Old password is incorrect."


def test_put_user_password_with_incorecrt_old_password(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user password without old password.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    tokens = signed_in_user
    data = {
        'old_password': 'IncorrectOldPassword123#',
        'password': 'Example123#',
        'confirm_password': 'Example123#'
    }
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Old password is incorrect."


def test_put_user_password_mismatch(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user password with mismatching password.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example123#',
        'confirm_password': 'Example1234#',
    }
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "Password and confirm_password fields do not match."


def test_put_user_password_length(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user password with a short password.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Exa12#',
        'confirm_password': 'Exa12#',
    }
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must be at least 8 characters long."


def test_put_user_password_without_digit(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user with a password without digits.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example#$',
        'confirm_password': 'Example#$',
    }
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one digit."


def test_put_user_password_without_special_char(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user with a password without special character.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    data = {
        'old_password': 'Password123#',
        'password': 'Example123',
        'confirm_password': 'Example123',
    }
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one special character."


def test_put_user_password_without_letters(mock_verification_email_task, client, user, signed_in_user):
    """
    Test update user with a password without letters.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    data = {
        'old_password': 'Password123#',
        'password': '12345678#',
        'confirm_password': '12345678#',
    }
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    mock_verification_email_task.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['code'] == 400
    assert response.data['status'] == "error"
    assert response.data['message'] == "User update failed."
    assert response.data['errors']['password']
    assert response.data['errors']['password'][0] == "Password must contain at least one letter."


def test_put_user_by_another_user(client, signed_in_user):
    """
    Test update user by another user.
    """
    new_user = User.objects.create_user(
        email="new_user@email.com",
        password="Password123#")
    url = reverse('user', kwargs={'user_id': new_user.id})
    data = {
        'email': 'new_email@email.com',
        'password': '12345678#',
        'confirm_password': '12345678#',
    }
    tokens = signed_in_user
    client.cookies['access_token'] = tokens['access_token']
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['code'] == 403
    assert response.data['status'] == "error"
    assert response.data['message'] == "You do not have permission to perform this action."

def test_put_user_without_access_token(client, user):
    """
    Test update user without access token.
    """
    url = reverse('user', kwargs={'user_id': user.id})
    data = {
        'email': 'new_email@email.com',
        'password': '12345678#',
        'confirm_password': '12345678#',
    }
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['code'] == 401
    assert response.data['status'] == "error"
    assert response.data['message'] == "Authentication credentials were not provided."


# =============================================================================
# TEST DELETE USER
# =============================================================================
def test_delete_user(client, user, signed_in_user):
    """
    Test delete user.
    """
    url  = reverse('user', kwargs={'user_id': user.id})
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    

def test_delete_user_by_another_user(client, signed_in_user):
    """
    Test delete user by another user.
    """
    user = User.objects.create_user(
        email="test-user@email.com",
        password="Password123#")
    url = reverse('user', kwargs={'user_id': user.id})
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['status'] == "error"
    assert response.data['code'] == 403
    assert response.data['message'] == "You do not have permission to perform this action."


def test_delete_user_with_invalid_id(client, signed_in_user):
    """
    Test delete user with invalid id.
    """
    url = reverse('user', kwargs={'user_id': "45678909876543"})
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['status'] == "error"
    assert response.data['code'] == 400
    assert response.data['message'] == "Invalid user id."


def test_delete_user_with_non_existent_id(client, signed_in_user):
    """
    Test delete user with non-existent id.
    """
    url = reverse('user', kwargs={'user_id': uuid.uuid4()})
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "User not found."


def test_delete_admin_user(client, admin_user, signed_in_user):
    """
    Test delete admin user by regular user.
    Admin users cannot be accessed from the url for reg user.
    """
    url = reverse('user', kwargs={'user_id': admin_user.id})
    client.cookies['access_token'] = signed_in_user['access_token']
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['status'] == "error"
    assert response.data['code'] == 404
    assert response.data['message'] == "User not found."
