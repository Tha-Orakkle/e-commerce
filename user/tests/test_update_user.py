from django.urls import reverse
from rest_framework import status

import pytest


# test update user email by both customer, shop owner, staff -done
# test update with the same email address. Check is_verified attr - done
# test update staff handle by customer, shopowner and shop_staff -done
# test update user email and staff handle by shop owner - done
# test update user email and staff handle by customer - done
# test update user email and staff handle by staff - done

# test update shop staff handle by shop owner -done
# test update staff handle with existing handle - done
# test update endpoint with missing data - done
# test update endpoint with invalid data data
# test update endpoint with unauthenticated user



# ==========================================================
# UPDATE USER (email/staff handle)
# ==========================================================

UPDATE_URL = reverse('user-me-update') 

@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner'],
    ids=['customer', 'shopowner']
)
def test_update_user_email_by_customer_and_shopowner(client, request, all_users, user_type):
    """
    Test updating customer and shopowner email address.
    """
    mock_verification_mail = request.getfixturevalue('mock_verification_email_task')
    user = all_users[user_type]
    old_email = user.email
    user.is_verified = True
    user.save(update_fields=['is_verified'])
    
    client.force_authenticate(user=user)
    data = {'email': 'new_email@email.com'}
    
    res = client.patch(UPDATE_URL, data=data, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "User updated successfully."
    assert 'data' in res.data
    assert res.data['data']['email'] != old_email
    assert res.data['data']['email'] == data['email']
    assert res.data['data']['is_verified'] == False
    mock_verification_mail.assert_called_once()


@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner'],
    ids=['customer', 'shopowner']
)
def test_update_user_email_by_customer_and_shopowner_with_same_email(client, request, all_users, user_type):
    """
    Test updating customer and shop owner email address with the same email.
    """
    mock_verification_mail = request.getfixturevalue('mock_verification_email_task')
    user = all_users[user_type]
    user.is_verified = True
    user.save(update_fields=['is_verified'])
    
    client.force_authenticate(user=user)
    data = {'email': user.email}
    
    res = client.patch(UPDATE_URL, data=data, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "User updated successfully."
    assert 'data' in res.data
    assert res.data['data']['is_verified'] == True
    mock_verification_mail.assert_not_called()
    
    
def test_update_staff_handle_by_shopowner(client, request, shopowner):
    """
    Test update the staff handle by the shopowner.
    """
    mock_verification_mail = request.getfixturevalue('mock_verification_email_task')
    old_handle = shopowner.staff_handle
    shopowner.is_verified = True
    shopowner.save(update_fields=['is_verified'])
    client.force_authenticate(user=shopowner)
    data = {'staff_handle': 'new_staff_handle'}

    res = client.patch(UPDATE_URL, data=data, format='json')
    
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "User updated successfully."
    assert 'data' in res.data
    assert res.data['data']['staff_handle'] != old_handle
    assert res.data['data']['staff_handle'] == data['staff_handle']
    mock_verification_mail.assert_not_called()

def test_update_staff_handle_by_customer(client, request, customer):
    """
    Test update staff handle by customer.
    Customers do not have staff handle. So, it is skipped and only email is checked for update.
    """
    mock_verification_mail = request.getfixturevalue('mock_verification_email_task')
    client.force_authenticate(user=customer)
    data = {'staff_handle': 'new_staff_handle'}

    res = client.patch(UPDATE_URL, data=data, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User update failed."
    assert 'errors' in res.data
    assert res.data['errors']['email'] == ['This field is required.']
    
    customer.refresh_from_db()
    assert customer.staff_handle == None
    
def test_update_email_and_staff_handle_by_customer(client, customer):
    """
    Test update a customer's email and staff handle.
    NB: Customers do have staff handle. This will be skipped.
    """
    old_email = customer.email
    client.force_authenticate(user=customer)
    
    data = {
        'email': 'new_email@email.com',
        'staff_handle': 'new_handle'
    }
    res = client.patch(UPDATE_URL, data=data, format='json')
    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "User updated successfully."
    assert 'data' in res.data
    assert res.data['data']['email'] != old_email
    assert res.data['data']['email'] == data['email']
    assert res.data['data']['staff_handle'] == None

def test_update_email_and_staff_handle_by_shop_staff(client, shop_staff):
    """
    Test updating email and staff handle by a shop staff.
    """
    client.force_authenticate(user=shop_staff)
    data = {'email': 'new_email@email.com'}

    res = client.patch(UPDATE_URL, data=data, format='json')
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."



@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner'],
    ids=['customer', 'shopowner']
)
def test_update_user_email_with_existing_email_address(client, all_users, user_type, customer_factory):
    """
    Test updating email address with existing email address.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)
    c1 = customer_factory()
    data = {'email': c1.email}

    res = client.patch(UPDATE_URL, data=data, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User update failed."
    assert 'errors' in res.data
    assert 'email' in res.data['errors']
    assert res.data['errors']['email'] == ["User with email already exists."]
    
def test_update_user_staff_handle_with_existing_staff_handle_in_the_same_shop(client, shopowner, shop_staff_factory):
    """
    Test update user staff handle with handles that already exist in the shop
    """
    s1 = shop_staff_factory(shopowner=shopowner)    
    data = {'staff_handle': s1.staff_handle}

    client.force_authenticate(user=shopowner)
    res = client.patch(UPDATE_URL, data=data, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User update failed."
    assert 'errors' in res.data
    assert 'staff_handle' in res.data['errors']
    assert res.data['errors']['staff_handle'] == ["Staff member with staff handle already exists."]


def test_update_user_with_missing_data_by_shopowner(client, shopowner):
    """
    Test update user with missing data by the shopowner.
    """
    
    client.force_authenticate(user=shopowner)
    res = client.patch(UPDATE_URL, data={}, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User update failed."
    assert 'errors' in res.data
    assert 'non_field_errors' in res.data['errors']
    assert res.data['errors']['non_field_errors'] == ["Either 'email' or 'staff_handle' is field is required."]

def test_update_user_with_missing_data_by_customer(client, customer):
    """
    Test update user with missing data by customer.
    """
    
    client.force_authenticate(user=customer)
    res = client.patch(UPDATE_URL, data={}, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User update failed."
    assert 'errors' in res.data
    assert 'email' in res.data['errors']
    assert res.data['errors']['email'] == ["This field is required."]


@pytest.mark.parametrize(
    'user_type',
    ['customer', 'shopowner'],
    ids=['customer', 'shopowner']
)
def test_update_user_with_invalid_email(client, all_users, user_type):
    """
    Test update user email with invalid email address.
    """
    user = all_users[user_type]

    client.force_authenticate(user=user)
    data = {'email': 'invalid_email'}
    res = client.patch(UPDATE_URL, data=data, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User update failed."
    assert 'errors' in res.data
    assert res.data['errors']['email'] == ["Enter a valid email address."]
    
def test_update_user_with_invalid_staff_handle(client, shopowner):
    """
    Test update user email with invalid staff handle.
    """
    client.force_authenticate(user=shopowner)
    data = {'staff_handle': 'JJ'} # too short
    res = client.patch(UPDATE_URL, data=data, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User update failed."
    assert 'errors' in res.data
    assert res.data['errors']['staff_handle'] == ["Ensure this field has at least 3 characters."]
    
    
    data = {'staff_handle': 'J' * 21} # too long
    res = client.patch(UPDATE_URL, data=data, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert res.data['message'] == "User update failed."
    assert 'errors' in res.data
    assert res.data['errors']['staff_handle'] == ["Ensure this field has no more than 20 characters."]
  
  
def test_update_user_by_unauthenticated_user(client):
    """
    Test update user by unauthenticated user.
    """
    data = {'email': 'new_email@email.com'}
    res = client.patch(UPDATE_URL, data=data, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Authentication credentials were not provided."
    
    client.cookies['access_token'] = 'invalid_token'
    
    res = client.patch(UPDATE_URL, data=data, format='json')
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"
    