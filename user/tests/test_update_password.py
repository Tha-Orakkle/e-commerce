from django.urls import reverse
from rest_framework import status

import pytest

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
# UPDATE_STAFF_PASSWORD_BY_SHOPOWNER_URL = lambda shop_id, staff_id: reverse('shop-staff-password', args=[shop_id, staff_id])
