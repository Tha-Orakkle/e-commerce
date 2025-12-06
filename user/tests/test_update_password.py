from django.urls import reverse
from rest_framework import status

import pytest
import uuid

# ==========================================================
# UPDATE PASSWORD TESTS (ALL USER TYPES)
# ==========================================================
UPDATE_PASSWORD_URL = reverse('user-me-password')


@pytest.mark.parametrize(
    "user_type, new_password",
    [
        ('customer', 'NewCustomerPass123!'),
        ('shopowner', 'NewShopOwnerPass123!'),
        ('shop_staff', 'NewStaffPass123!'),
    ],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_password(client, all_users, user_type, new_password):
    """
    Test update password by users of all types.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)

    payload = {
        'old_password': 'Password123#',
        'new_password': new_password,
        'confirm_password': new_password
    }

    res = client.patch(UPDATE_PASSWORD_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Password changed successfully."

    user.refresh_from_db()
    assert user.check_password(new_password) is True
    assert user.check_password(payload['old_password']) is False


@pytest.mark.parametrize(
    "user_type",
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_password_fails_with_wrong_old_password(client, all_users, user_type):
    """
    Test update password fails with wrong old password.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)

    payload = {
        'old_password': 'WrongOldPassword!',
        'new_password': 'NewPassword123!',
        'confirm_password': 'NewPassword123!'
    }
    res = client.patch(UPDATE_PASSWORD_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert 'old_password' in res.data['errors']
    assert res.data['errors']['old_password'][0] == "Old password is incorrect."


@pytest.mark.parametrize(
    "user_type",
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_password_fails_with_mismatched_new_passwords(client, all_users, user_type):
    """
    Test update password fails with mismatched new passwords.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)

    payload = {
        'old_password': 'Password123#',
        'new_password': 'NewPassword123!',
        'confirm_password': 'DifferentNewPassword123!'
    }
    res = client.patch(UPDATE_PASSWORD_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert 'non_field_error' in res.data['errors']
    assert res.data['errors']['non_field_error'] == ["Passwords do not match."]


def test_unauthenticated_user_cannot_update_password(client):
    """
    Test that an unauthenticated user cannot update password.
    """
    payload = {
        'old_password': 'Password123#',
        'new_password': 'NewPassword123!',
        'confirm_password': 'NewPassword123!'
    }
    res = client.patch(UPDATE_PASSWORD_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['message'] == "Authentication credentials were not provided."


@pytest.mark.parametrize(
    "user_type",
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_password_fails_with_weak_new_password(client, all_users, user_type):
    """
    Test update password fails with weak new password.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)

    payload = {
        'old_password': 'Password123#',
        'new_password': 'weak',
        'confirm_password': 'weak'
    }
    res = client.patch(UPDATE_PASSWORD_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert 'new_password' in res.data['errors']
    assert len(res.data['errors']['new_password']) > 0


@pytest.mark.parametrize(
    "user_type",
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_password_fails_with_missing_fields(client, all_users, user_type):
    """
    Test update password fails with missing fields.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)

    payload = {
        # 'old_password' is missing
        'new_password': 'NewPassword123!',
        'confirm_password': 'NewPassword123!'
    }
    res = client.patch(UPDATE_PASSWORD_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert 'old_password' in res.data['errors']
    assert res.data['errors']['old_password'] == ["This field is required."]

    payload = {
        'old_password': 'Password123#',
        # 'new_password' and 'confirm_password' are missing
    }
    res = client.patch(UPDATE_PASSWORD_URL, data=payload, format='json')
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert 'new_password' in res.data['errors']
    assert 'confirm_password' in res.data['errors']
    assert res.data['errors']['new_password'] == ["This field is required."]
    assert res.data['errors']['confirm_password'] == ["This field is required."]


@pytest.mark.parametrize(
    "user_type",
    ['customer', 'shopowner', 'shop_staff'],
    ids=['customer', 'shopowner', 'shop_staff']
)
def test_update_password_fails_with_blank_fields(client, all_users, user_type):
    """
    Test update password fails with missing fields.
    """
    user = all_users[user_type]
    client.force_authenticate(user=user)

    payload = {
        'old_password': '',
        'new_password': '',
        'confirm_password': ''
    }
    res = client.patch(UPDATE_PASSWORD_URL, data=payload, format='json')

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] == "error"
    assert res.data['code'] == "validation_error"
    assert 'old_password' in res.data['errors']
    assert res.data['errors']['old_password'] == ["This field may not be blank."]
    assert res.data['errors']['new_password'] == ["This field may not be blank."]
    assert res.data['errors']['confirm_password'] == ["This field may not be blank."]

# ==========================================================
# UPDATE SHOP STAFF PASSWORD BY SHOPOWNER TESTS
# ==========================================================
def generate_update_staff_password_by_shopowner_url(shop_id, staff_id):
    return reverse('shop-staff-password', args=[shop_id, staff_id])

STAFF_PASSWORD_UPDATE_DATA = {
        'new_password': 'NewStaffPassword123!',
        'confirm_password': 'NewStaffPassword123!'
}


def test_shopowner_can_update_staff_password(client, shopowner, shop_staff_factory):
    """
    Test that a shop owner can update a staff member's password.
    """
    shop_staff = shop_staff_factory(shopowner=shopowner)

    client.force_authenticate(user=shopowner)

    url = generate_update_staff_password_by_shopowner_url(
        shop_id=shopowner.owned_shop.id,
        staff_id=shop_staff.id
    )
    payload = STAFF_PASSWORD_UPDATE_DATA

    res = client.patch(url, data=payload, format='json')

    assert res.status_code == status.HTTP_200_OK
    assert res.data['status'] == "success"
    assert res.data['message'] == "Staff password changed successfully."

    shop_staff.refresh_from_db()
    assert shop_staff.check_password(payload['new_password']) is True
    assert shop_staff.check_password('Password123#') is False

def test_shopowner_cannot_update_staff_password_of_other_shop(client, shopowner_factory, shop_staff_factory):
    """
    Test that a shop owner cannot update a staff member's password
    for a staff member that does not belong to their shop.
    """
    shopowner1 = shopowner_factory()
    shopowner2 = shopowner_factory()
    sh1_staff = shop_staff_factory(shopowner=shopowner1)
    
    client.force_authenticate(user=shopowner2)

    url = generate_update_staff_password_by_shopowner_url(
        shop_id=sh1_staff.shop.id,
        staff_id=sh1_staff.id
    )
    res = client.patch(url, data=STAFF_PASSWORD_UPDATE_DATA, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['status'] == "error"
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."

def test_non_shopowner_cannot_update_staff_password(client, shopowner, shop_staff_factory):
    """
    Test that a non-shopowner user cannot update a staff member's password.
    """
    shop_staff1 = shop_staff_factory(shopowner=shopowner)
    shop_staff2 = shop_staff_factory(shopowner=shopowner)
    
    client.force_authenticate(user=shop_staff1)
    
    url = generate_update_staff_password_by_shopowner_url(
        shop_id=shopowner.owned_shop.id,
        staff_id=shop_staff2.id
    )
    res = client.patch(url, data=STAFF_PASSWORD_UPDATE_DATA, format='json')

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data['code'] == "forbidden"
    assert res.data['message'] == "You do not have permission to perform this action."
    
def test_update_staff_password_fails_with_non_existent_shop_id(client, shopowner, shop_staff_factory):
    """
    Test that updating staff password fails with non-existent shop ID.
    """
    shop_staff = shop_staff_factory(shopowner=shopowner)

    client.force_authenticate(user=shopowner)

    url = generate_update_staff_password_by_shopowner_url(
        shop_id=uuid.uuid4(), 
        staff_id=shop_staff.id
    )
    res = client.patch(url, data=STAFF_PASSWORD_UPDATE_DATA, format='json')

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No shop matching the given ID found."
    
def test_update_staff_password_fails_with_non_existent_staff_id(client, shopowner):
    """
    Test that updating staff password fails with non-existent shop ID.
    """
    client.force_authenticate(user=shopowner)

    url = generate_update_staff_password_by_shopowner_url(
        shop_id=shopowner.owned_shop.id,
        staff_id=uuid.uuid4()
    )

    res = client.patch(url, data=STAFF_PASSWORD_UPDATE_DATA, format='json')

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data['status'] == "error"
    assert res.data['code'] == "not_found"
    assert res.data['message'] == "No staff member matching given ID found."
    
def test_update_staff_password_fails_with_invalid_shop_and_staff_ids(client, shopowner, shop_staff_factory):
    """
    Test that updating staff password fails with invalid staff and shop uuid
    """
    shop_staff = shop_staff_factory(shopowner=shopowner)
    client.force_authenticate(user=shopowner)

    # invalid shop id
    url = generate_update_staff_password_by_shopowner_url(
        shop_id = 'invalid_id',
        staff_id = shop_staff.id 
    )
    res = client.patch(url, data=STAFF_PASSWORD_UPDATE_DATA, format='json' )
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid shop id."
    
    # invalid staff id
    url = generate_update_staff_password_by_shopowner_url(
        shop_id = shopowner.owned_shop.id,
        staff_id = 'invalid_id'
    )
    res = client.patch(url, data=STAFF_PASSWORD_UPDATE_DATA, format='json' )
    assert res.data['status'] == "error"
    assert res.data['code'] == "invalid_uuid"
    assert res.data['message'] == "Invalid staff id."
    
    
def test_update_staff_password_fails_with_mismatched_passwords(client, shopowner, shop_staff):
    """
    Test that updating staff password fails with mismatched passwords
    """
    client.force_authenticate(user=shopowner)
    
    payload = {
        'new_password': 'NewPassword123!',
        'confirm_password': 'AnotherPassword123!'
    }
    url = generate_update_staff_password_by_shopowner_url(
        shop_id=shopowner.owned_shop.id,
        staff_id=shop_staff.id
    )
    
    res = client.patch(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] ==  "error"
    assert res.data['code'] ==  "validation_error"
    assert res.data['message'] ==  "Staff password change failed."
    assert 'non_field_error' in res.data['errors']
    assert res.data['errors']['non_field_error'] ==  ["Passwords do not match."]


def test_update_staff_password_fails_with_missing_values(client, shopowner, shop_staff):
    """
    Test that updating staff password fails with missing password values.
    """
    client.force_authenticate(user=shopowner)
    
    payload = {}
    url = generate_update_staff_password_by_shopowner_url(
        shop_id=shopowner.owned_shop.id,
        staff_id=shop_staff.id
    )
    
    res = client.patch(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] ==  "error"
    assert res.data['code'] ==  "validation_error"
    assert res.data['message'] ==  "Staff password change failed."
    assert 'new_password' in res.data['errors']
    assert 'confirm_password' in res.data['errors']
    assert res.data['errors']['new_password'] ==  ["This field is required."]
    assert res.data['errors']['confirm_password'] ==  ["This field is required."]
    
def test_update_staff_password_fails_with_blank_values(client, shopowner, shop_staff):
    """
    Test that updating staff password fails with blank password values.
    """
    client.force_authenticate(user=shopowner)
    
    payload = {
        'new_password': '',
        'confirm_password': '',
    }
    url = generate_update_staff_password_by_shopowner_url(
        shop_id=shopowner.owned_shop.id,
        staff_id=shop_staff.id
    )
    
    res = client.patch(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] ==  "error"
    assert res.data['code'] ==  "validation_error"
    assert res.data['message'] ==  "Staff password change failed."
    assert 'new_password' in res.data['errors']
    assert 'confirm_password' in res.data['errors']
    assert res.data['errors']['new_password'] ==  ["This field may not be blank."]
    assert res.data['errors']['confirm_password'] ==  ["This field may not be blank."]

def test_update_password_fails_with_weak_password(client, shopowner, shop_staff):
    """
    Test updating staff password fails with weak password
    """
    client.force_authenticate(user=shopowner)
    
    payload = {
        'new_password': 'weak_password',
        'confirm_password': 'weak_password',
    }
    url = generate_update_staff_password_by_shopowner_url(
        shop_id=shopowner.owned_shop.id,
        staff_id=shop_staff.id
    )
    
    res = client.patch(url, data=payload, format='json')
    
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data['status'] ==  "error"
    assert res.data['code'] ==  "validation_error"
    assert res.data['message'] ==  "Staff password change failed."
    assert 'new_password' in res.data['errors']
    assert len(res.data['errors']['new_password']) > 1