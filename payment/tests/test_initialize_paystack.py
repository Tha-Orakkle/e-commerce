from django.utils.timezone import now
from django.urls import reverse
from rest_framework import status

import pytest
import requests
import uuid

from order.models import PaymentMethod, OrderGroupStatus
from payment.domain.exceptions import PaystackError

PAYMENT_PAYLOAD = {"service": "paystack"}


# ================================================================
# TEST INITIALIZING PAYMENT
# ================================================================
@pytest.mark.parametrize(
    "invalid_service",
    ["invalid_service", "paypal", 123, 123.45],
    ids=[
        "invalid_service",
        "paypal",
        "integer",
        "float",
    ]
)
def test_initialize_payment_with_non_supported_service(
    client,
    customer,
    invalid_service
):
    """
    Test that initializing payment with non-supported service fails.
    """
    payload = {"service": invalid_service}

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[uuid.uuid4()])
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "validation_error"
    assert data["message"] == "Payment initialization failed."
    assert "errors" in data
    assert "service" in data["errors"]
    expected_msg = [f"{invalid_service} is not a supported service type."]
    assert data["errors"]["service"] == expected_msg


@pytest.mark.parametrize(
    "invalid_service",
    [True, False, [], {}],
    ids=["True", "False", "empty_list", "empty_dict"]
)
def test_initialize_payment_with_non_string_service(
    client,
    customer,
    invalid_service
):
    """
    Test that initializing payment with non-string service fails.
    """
    payload = {"service": invalid_service}

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[uuid.uuid4()])
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "validation_error"
    assert data["message"] == "Payment initialization failed."
    assert "errors" in data
    assert "service" in data["errors"]
    assert data["errors"]["service"] == ["Not a valid string."]


def test_initialize_payment_with_blank_service(
    client,
    customer
):
    """
    Test that initializing payment with blank service fails.
    """
    payload = {"service": ""}

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[uuid.uuid4()])
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "validation_error"
    assert data["message"] == "Payment initialization failed."
    assert "errors" in data
    assert "service" in data["errors"]
    assert data["errors"]["service"] == ["This field may not be blank."]


def test_initialize_payment_with_null_service(
    client,
    customer
):
    """
    Test that initializing payment with null service fails.
    """
    payload = {"service": None}

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[uuid.uuid4()])
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "validation_error"
    assert data["message"] == "Payment initialization failed."
    assert "errors" in data
    assert "service" in data["errors"]
    assert data["errors"]["service"] == ["This field may not be null."]


def test_initialize_payment_with_missing_service(
    client,
    customer
):
    """
    Test that initializing payment with missing service fails.
    """
    payload = {}

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[uuid.uuid4()])
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "validation_error"
    assert data["message"] == "Payment initialization failed."
    assert "errors" in data
    assert "service" in data["errors"]
    assert data["errors"]["service"] == ["This field is required."]


def test_initialize_payment_with_invalid_order_group_id(
    client,
    customer
):
    """
    Test that initializing payment with invalid order group id fails.
    """
    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=["invalid-uuid"])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "invalid_uuid"
    assert data["message"] == "Invalid order group id."


def test_initialize_payment_with_non_existent_order_group_id(
    client,
    customer
):
    """
    Test that initializing payment with non-existent order group id fails.
    """
    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[uuid.uuid4()])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_404_NOT_FOUND
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "not_found"
    assert data["message"] == "No order group matching the given ID found."


def test_initialize_payment_for_order_group_with_cash_payment_method(
    client,
    customer,
    order_group_factory
):
    """
    Test that initializing payment for order group with cash payment
    method fails.
    """
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.CASH
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "invalid_payment_method"
    assert data["message"] == ("Payment can only be initialized for order "
                               "groups with DIGITAL payment method.")


@pytest.mark.parametrize(
    "group_status",
    [s[0] for s in OrderGroupStatus.choices
     if s[0] != OrderGroupStatus.PENDING],
    ids=[s[0] for s in OrderGroupStatus.choices
         if s[0] != OrderGroupStatus.PENDING]
)
def test_initialize_payment_for_order_group_with_non_pending_status(
    client,
    customer,
    order_group_factory,
    group_status
):
    """
    Test that initializing payment for order group with non-pending
    status fails.
    """
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL,
        status=group_status
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "invalid_order_group_status"
    assert data["message"] == "Only pending order groups can be paid for."


def test_initialize_payment_for_already_paid_order_group_(
    client,
    customer,
    order_group_factory,
    payment_factory
):
    """
    Test that initializing payment for order group that has
    already been paid fails.
    """
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL,
    )
    payment = payment_factory(
        user=customer,
        group=group,
        verified=True,
        paid_at=now()
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "duplicate_transaction"
    assert data["message"] == "Payment has already been verified."


def test_initialize_payment_for_order_group_with_existing_payment_instance(
    client,
    mocker,
    customer,
    order_group_factory,
    payment_factory,
    mock_paystack_post
):
    """
    Test that initializing payment for order group that has an existing
    payment instance but not verified succeeds.
    The payment reference should be updated.
    """
    mock_response = mocker.Mock()
    mock_response.raise_for_response.return_value = None
    mock_response.json.return_value = {
        "status": True,
        "data": {"authorization_url": "..."}
    }
    mock_paystack_post.return_value = mock_response

    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL,
    )
    payment = payment_factory(
        user=customer,
        group=group,
        verified=False,
        paid_at=None
    )
    old_reference = payment.reference

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    assert res.data["message"] == "Payment initialized successfully."
    payment.refresh_from_db()
    assert payment.reference != old_reference


# ================================================================
# TEST INITIALIZING PAYMENT - AUTHORIZATION
# ================================================================
@pytest.mark.parametrize(
    "user_type",
    ["shopowner", "shop_staff"],
    ids=["shopowner", "shop_staff"]
)
def test_initialize_payment_by_non_customer_user(
    client,
    all_users,
    order_group_factory,
    user_type
):
    """
    Test that initializing payment by non-customer user fails.
    """
    user = all_users[user_type]
    group = order_group_factory(
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=user)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_403_FORBIDDEN
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "forbidden"
    expected_msg = "You do not have permission to perform this action."
    assert data["message"] == expected_msg


def test_initialize_payment_by_different_user(
    client,
    customer,
    order_group_factory,
):
    """
    Test that initializing payment by a different user fails.
    """
    group = order_group_factory(
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_404_NOT_FOUND
    data = res.data
    assert data["status"] == "error"
    assert data["code"] == "not_found"
    assert data["message"] == "No order group matching the given ID found."


def test_initialize_payment_by_superuser(
    client,
    mocker,
    super_user,
    order_group_factory,
    mock_paystack_post
):
    """
    Test that initializing payment by super user succeeds.
    """
    mock_response = mocker.Mock()
    mock_response.raise_for_response.return_value = None
    mock_response.json.return_value = {
        "status": True,
        "data": {"authorization_url": "..."}
    }
    mock_paystack_post.return_value = mock_response
    group = order_group_factory(
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=super_user)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_200_OK
    data = res.data
    assert data["status"] == "success"


def test_initialize_payment_by_unauthenticated_user(client):
    """
    Test initializing payment by an unauthenticated user fails.
    Test no access token provided and invalid token.
    """
    url = reverse("initialize-payment", args=[uuid.uuid4()])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    expected_msg = "Authentication credentials were not provided."
    assert res.data['message'] == expected_msg

    client.cookies["access_token"] = "invalid_token"
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data['status'] == "error"
    assert res.data['code'] == "unauthorized"
    assert res.data['message'] == "Token is invalid or expired"


# ================================================================
# TEST PAYSTACK
# ================================================================
def test_initialize_payment_with_paystack(
    client,
    mocker,
    customer,
    order_group_factory,
    mock_paystack_post,
):
    """
    Test that initializing payment with paystack succeeds.
    """
    mock_response = mocker.Mock()
    mock_response.raise_for_response.return_value = None
    mock_response.json.return_value = {
        "status": True,
        "data": {"authorization_url": "..."}
    }
    mock_paystack_post.return_value = mock_response

    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"
    assert res.data["message"] == "Payment initialized successfully."
    data = res.data["data"]
    assert "authorization_url" in data
    assert data["authorization_url"] is not None


@pytest.mark.parametrize(
    "service_type",
    ["PAYSTACK", "Paystack", "paystack", "PAyStacK"],
    ids=["PAYSTACK", "Paystack", "paystack", "PAyStacK"]
)
def test_initialize_payment_with_paystack_service_type_case_insensitive(
    client,
    mocker,
    customer,
    order_group_factory,
    mock_paystack_post,
    service_type
):
    """
    Test that initializing payment with paystack service type succeeds.
    Test paystack service type works regardless of case used.
    """
    mock_response = mocker.Mock()
    mock_response.raise_for_response.return_value = None
    mock_response.json.return_value = {
        "status": True,
        "data": {"authorization_url": "..."}
    }
    mock_paystack_post.return_value = mock_response

    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    payload = {"service": service_type}

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])
    res = client.post(url, data=payload, format="json")

    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == "success"


@pytest.mark.parametrize(
    "status_code",
    [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        status.HTTP_429_TOO_MANY_REQUESTS,
    ],
    ids=[
        "400_bad_request",
        "401_unauthorized",
        "403_forbidden",
        "404_not_found",
        "409_conflict",
        "429_too_many_requests"
    ]
)
def test_initialize_payment_with_paystack_with_4xx_response(
    client,
    mocker,
    customer,
    order_group_factory,
    mock_paystack_post,
    status_code
):
    """
    Test initializing paystack fails when paystack service returns
    4xx errors.
    """
    mock_response = mocker.Mock()
    mock_response.status_code = status_code
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        response=mock_response
    )
    mock_paystack_post.return_value = mock_response
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])

    res = client.post(url, PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_502_BAD_GATEWAY
    assert res.data["status"] == "error"
    assert res.data["code"] == "paystack_request_rejected"
    assert res.data["message"] == ("Unable to process your request due to "
                                   "an error communicating with Paystack.")


@pytest.mark.parametrize(
    "status_code",
    [
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        status.HTTP_502_BAD_GATEWAY,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ],
    ids=[
        "500_internal_server_error",
        "502_bad_gateway",
        "503_service_unavailable"
    ]
)
def test_initialize_payment_with_paystack_with_5xx_response(
    client,
    mocker,
    customer,
    order_group_factory,
    mock_paystack_post,
    status_code
):
    """
    Test initializing paystack fails when paystack service returns
    5xx errors.
    """
    mock_response = mocker.Mock()
    mock_response.status_code = status_code
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        response=mock_response
    )
    mock_paystack_post.return_value = mock_response
    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])

    res = client.post(url, PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert res.data["status"] == "error"
    assert res.data["code"] == "paystack_service_unavailable"
    expected_msg = "Payment service is temporarily unavailable."
    assert res.data["message"] == expected_msg


def test_initialize_payment_with_paystack_with_malformed_json(
    client,
    mocker,
    customer,
    order_group_factory,
    mock_paystack_post,
):
    """
    Test initializing paystack fails when paystack service returns
    malformed JSON.
    """
    mock_response = mocker.Mock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.raise_for_status.side_effect = None
    mock_response.json.side_effect = requests.JSONDecodeError(
        "Expecting value", "", 0
    )
    mock_paystack_post.return_value = mock_response

    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])

    res = client.post(url, PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_502_BAD_GATEWAY
    assert res.data["status"] == "error"
    assert res.data["code"] == "invalid_paystack_response"
    expected_msg = "Received an invalid response from the Paystack."
    assert res.data["message"] == expected_msg


def test_initialize_payment_with_paystack_where_connection_timeouts(
    client,
    customer,
    order_group_factory,
    mock_paystack_post,
):
    """
    Test initializing paystack fails when paystack service returns
    connection timeouts.
    """
    mock_paystack_post.side_effect = requests.Timeout()

    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])

    res = client.post(url, PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert res.data["status"] == "error"
    assert res.data["code"] == "paystack_timeout"
    expected_msg = "Paystack timed out. Please try again."
    assert res.data["message"] == expected_msg


def test_initialize_payment_with_paystack_where_connection_fails(
    client,
    customer,
    order_group_factory,
    mock_paystack_post,
):
    """
    Test initializing paystack fails when paystack service returns
    connection failures.
    """
    mock_paystack_post.side_effect = requests.ConnectionError()

    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])

    res = client.post(url, PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert res.data["status"] == "error"
    assert res.data["code"] == "paystack_connection_error"
    expected_msg = "Failed to connect to Paystack. Please try again."
    assert res.data["message"] == expected_msg


def test_initialize_payment_with_paystack_where_request_fails(
    client,
    customer,
    order_group_factory,
    mock_paystack_post,
):
    """
    Test initializing paystack fails when paystack service request
    fails due to unexpected errors.
    """
    mock_paystack_post.side_effect = requests.RequestException()

    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])

    res = client.post(url, PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_502_BAD_GATEWAY
    assert res.data["status"] == "error"
    assert res.data["code"] == "paystack_request_failed"
    assert res.data["message"] == ("An unexpected error occurred while "
                                   "communicating with Paystack.")


def test_initialize_payment_with_paystack_where_response_status_is_false(
    client,
    mocker,
    customer,
    order_group_factory,
    mock_paystack_post,
):
    """
    Test initializing paystack fails when paystack service returns
    response with status=False.
    """
    mock_response = mocker.Mock()
    mock_response.raise_for_response.return_value = None
    mock_response.json.return_value = {
        "status": False,
        "message": "Invalid request."
    }
    mock_paystack_post.return_value = mock_response

    group = order_group_factory(
        user=customer,
        payment_method=PaymentMethod.DIGITAL
    )

    client.force_authenticate(user=customer)
    url = reverse("initialize-payment", args=[group.id])

    res = client.post(url, PAYMENT_PAYLOAD, format="json")

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["status"] == "error"
    assert res.data["code"] == "paystack_error"
    assert res.data["message"] == "Invalid request."
