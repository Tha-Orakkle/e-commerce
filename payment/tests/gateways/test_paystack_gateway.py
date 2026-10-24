import logging

import pytest
import requests
from rest_framework import status

from payment.domain.exceptions import (
    PaymentGatewayConnectionError,
    PaymentGatewayError,
    PaymentGatewayJSONError,
    PaymentGatewayTimeoutError,
)
from payment.gateways.paystack import PaystackGateway

POST_PATH = "payment.gateways.paystack.requests.post"
GET_PATH = "payment.gateways.paystack.requests.get"
PAYSTACK_LOGGER_NAME = "paymemt.gateways.paystack"

INIT_KWARGS = {
    "reference": "ref-123",
    "amount": 150000,
    "currency": "NGN",
    "email": "customer@example.com",
    "metadata": {"payment_id": "p1", "order_group_id": "g1"},
}


@pytest.fixture
def gateway():
    return PaystackGateway()


def ok_response(mocker, payload):
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


def http_error_response(mocker, status_code):
    response = mocker.Mock()
    response.status_code = status_code
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response
    )
    return response


# ==========================================================
# INITIALIZE PAYMENT
# ==========================================================
def test_initialize_payment_returns_provider_data(mocker, gateway):
    """
    Test that a successful initialization returns Paystack's data
    and sends the expected request body.
    """
    mock_post = mocker.patch(POST_PATH, return_value=ok_response(mocker, {
        "status": True,
        "data": {"authorization_url": "https://paystack.test/pay"}
    }))

    data = gateway.initialize_payment(**INIT_KWARGS)

    assert data == {"authorization_url": "https://paystack.test/pay"}
    sent = mock_post.call_args.kwargs
    assert sent["json"]["reference"] == "ref-123"
    assert sent["json"]["amount"] == 150000
    assert sent["json"]["currency"] == "NGN"
    assert sent["json"]["email"] == "customer@example.com"
    assert sent["json"]["metadata"] == INIT_KWARGS["metadata"]
    assert "callback_url" in sent["json"]
    assert sent["headers"]["Content-Type"] == "application/json"
    assert sent["headers"]["Authorization"].startswith("Bearer ")
    assert sent["timeout"] == PaystackGateway.TIMEOUT


@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 404, 409, 429],
    ids=[400, 401, 403, 404, 409, 429],
)
def test_initialize_payment_with_4xx_response(mocker, gateway, status_code):
    """
    Test that a 4xx response becomes a gateway error.
    """
    mocker.patch(POST_PATH, return_value=http_error_response(
        mocker, status_code
    ))

    with pytest.raises(PaymentGatewayError) as exc_info:
        gateway.initialize_payment(**INIT_KWARGS)

    assert exc_info.value.code == "payment_provider_request_rejected"
    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.parametrize(
    "status_code",
    [500, 502, 503],
    ids=[500, 502, 503],
)
def test_initialize_payment_with_5xx_response(mocker, gateway, status_code):
    """
    Test that a 5xx response becomes a service-unavailable error.
    """
    mocker.patch(POST_PATH, return_value=http_error_response(
        mocker, status_code
    ))

    with pytest.raises(PaymentGatewayError) as exc_info:
        gateway.initialize_payment(**INIT_KWARGS)

    assert exc_info.value.code == "payment_provider_service_unavailable"
    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 404, 409, 429, 500, 502, 503],
    ids=[400, 401, 403, 404, 409, 429, 500, 502, 503],
)
def test_initialize_payment_logs_http_errors(
    mocker,
    caplog,
    gateway,
    status_code
):
    mocker.patch(POST_PATH, return_value=http_error_response(
        mocker, status_code
    ))

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME
    ), pytest.raises(PaymentGatewayError):
        gateway.initialize_payment(**INIT_KWARGS)

    assert "Paystack returned an HTTP error" in caplog.text


def test_initialize_payment_with_malformed_json(mocker, gateway):
    """
    Test that an unparsable body becomes an invalid-response error.
    """
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = requests.JSONDecodeError("Expecting", "", 0)
    mocker.patch(POST_PATH, return_value=response)

    with pytest.raises(PaymentGatewayJSONError) as exc_info:
        gateway.initialize_payment(**INIT_KWARGS)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc_info.value.code == "invalid_payment_provider_response"
    assert exc_info.value.detail == (
        "Received an invalid JSON response from provider"
    )


def test_initialize_payment_logs_malformed_json_error(mocker, caplog, gateway):
    """
    Test that an unparseable body response is logged.
    """
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = requests.JSONDecodeError("Expecting", "", 0)
    mocker.patch(POST_PATH, return_value=response)

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME,
    ), pytest.raises(PaymentGatewayJSONError):
        gateway.initialize_payment(**INIT_KWARGS)

    assert "Paystack returned an invalid JSON response" in caplog.text


def test_initialize_payment_timeout_raises_timeout_error(mocker, gateway):
    """
    Regression: a timeout must raise PaymentGatewayTimeoutError (which
    the Celery task retries on), not a TypeError.
    """
    mocker.patch(POST_PATH, side_effect=requests.Timeout())

    with pytest.raises(PaymentGatewayTimeoutError) as exc_info:
        gateway.initialize_payment(**INIT_KWARGS)

    assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert exc_info.value.code == "payment_gateway_timeout"
    assert exc_info.value.detail == (
        "Payment provider timed out. Please try again"
    )


def test_initialize_payment_logs_timeout_error(mocker, caplog, gateway):
    """
    Test timeout error is logged.
    """
    mocker.patch(POST_PATH, side_effect=requests.Timeout())

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME
    ), pytest.raises(PaymentGatewayTimeoutError):
        gateway.initialize_payment(**INIT_KWARGS)

    assert "Paystack request timed out" in caplog.text


def test_initialize_payment_connection_error_raises_connection_error(
    mocker, gateway
):
    """
    Regression: a connection failure must raise
    PaymentGatewayConnectionError, not a TypeError.
    """
    mocker.patch(POST_PATH, side_effect=requests.ConnectionError())

    with pytest.raises(PaymentGatewayConnectionError) as exc_info:
        gateway.initialize_payment(**INIT_KWARGS)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.code == "payment_gateway_connection_error"
    assert exc_info.value.detail == (
        "Failed to connect to payment provider. Please try again."
    )


def test_initialize_payment_logs_connection_error(
    mocker, caplog, gateway
):
    """
    Test that connection failure is logged.
    """
    mocker.patch(POST_PATH, side_effect=requests.ConnectionError())

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME,
    ), pytest.raises(PaymentGatewayConnectionError):
        gateway.initialize_payment(**INIT_KWARGS)

    assert "Unable to connect to Paystack" in caplog.text


def test_initialize_payment_with_unexpected_request_error(mocker, gateway):
    """
    Test that any other requests error becomes a generic gateway error.
    """
    mocker.patch(POST_PATH, side_effect=requests.RequestException())

    with pytest.raises(PaymentGatewayError) as exc_info:
        gateway.initialize_payment(**INIT_KWARGS)

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc_info.value.code == "payment_provider_request_failed"
    assert exc_info.value.detail == (
        "An unexpected error occurred while "
        "communicating with payment provider."
    )


def test_initialize_payment_logs_unexpected_request_error(
    caplog, mocker, gateway
):
    """
    Test that any other requests error is logged.
    """
    mocker.patch(POST_PATH, side_effect=requests.RequestException())

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME
    ), pytest.raises(PaymentGatewayError):
        gateway.initialize_payment(**INIT_KWARGS)

    assert "Unexpected error communicating with Paystack" in caplog.text


def test_initialize_payment_with_false_status(mocker, gateway):
    """
    Test that status=False in the body is surfaced with its message.
    """
    mocker.patch(POST_PATH, return_value=ok_response(mocker, {
        "status": False,
        "message": "Invalid request."
    }))

    with pytest.raises(PaymentGatewayError) as exc_info:
        gateway.initialize_payment(**INIT_KWARGS)

    assert exc_info.value.detail == "Invalid request."
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_initialize_payment_logs_false_status_error(caplog, mocker, gateway):
    mocker.patch(POST_PATH, return_value=ok_response(mocker, {
        "status": False,
        "message": "Invalid request"
    }))

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME
    ), pytest.raises(PaymentGatewayError):
        gateway.initialize_payment(**INIT_KWARGS)

    assert "Paystack rejected the payment initialization" in caplog.text


# ==========================================================
# VERIFY PAYMENT
# ==========================================================
def test_verify_payment_returns_provider_data(mocker, gateway):
    """
    Test that a successful verification returns Paystack's data and
    queries the reference.
    """
    mock_get = mocker.patch(GET_PATH, return_value=ok_response(mocker, {
        "status": True,
        "data": {"status": "success", "reference": "ref-123"}
    }))

    data = gateway.verify_payment(reference="ref-123")

    assert data == {"status": "success", "reference": "ref-123"}
    assert mock_get.call_args.args[0].endswith("ref-123")
    assert mock_get.call_args.kwargs["timeout"] == PaystackGateway.TIMEOUT


@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 404, 409, 429],
    ids=[400, 401, 403, 404, 409, 429],
)
def test_verify_payment_with_4xx_response(mocker, gateway, status_code):
    """
    Test that a 4xx response becomes a gateway error.
    """
    mocker.patch(GET_PATH, return_value=http_error_response(
        mocker, status_code
    ))

    with pytest.raises(PaymentGatewayError) as exc_info:
        gateway.verify_payment(reference="ref-123")

    assert exc_info.value.code == "payment_provider_request_rejected"
    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.parametrize(
    "status_code",
    [500, 502, 503],
    ids=[500, 502, 503],
)
def test_verify_payment_with_5xx_response(mocker, gateway, status_code):
    """
    Test that a 5xx response becomes a service-unavailable error.
    """
    mocker.patch(GET_PATH, return_value=http_error_response(
        mocker, status_code
    ))

    with pytest.raises(PaymentGatewayError) as exc_info:
        gateway.verify_payment(reference="ref-123")

    assert exc_info.value.code == "payment_provider_service_unavailable"
    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 404, 409, 429, 500, 502, 503],
    ids=[400, 401, 403, 404, 409, 429, 500, 502, 503],
)
def test_verify_payment_logs_http_errors(
    mocker,
    caplog,
    gateway,
    status_code
):
    mocker.patch(POST_PATH, return_value=http_error_response(
        mocker, status_code
    ))

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME
    ), pytest.raises(PaymentGatewayError):
        gateway.verify_payment(reference="ref-123")

    assert "Paystack returned an HTTP error" in caplog.text


def test_verify_payment_with_malformed_json(mocker, gateway):
    """
    Test that an unparsable body becomes an invalid-response error.
    """
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = requests.JSONDecodeError("Expecting", "", 0)
    mocker.patch(GET_PATH, return_value=response)

    with pytest.raises(PaymentGatewayJSONError) as exc_info:
        gateway.verify_payment(reference="ref-123")

    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc_info.value.code == "invalid_payment_provider_response"
    assert exc_info.value.detail == (
        "Received an invalid JSON response from provider"
    )


def test_verify_payment_logs_malformed_json_error(mocker, caplog, gateway):
    """
    Test that an unparseable body response is logged.
    """
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = requests.JSONDecodeError("Expecting", "", 0)
    mocker.patch(GET_PATH, return_value=response)

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME,
    ), pytest.raises(PaymentGatewayJSONError):
        gateway.verify_payment(reference="ref-123")

    assert "Paystack returned an invalid JSON response" in caplog.text


def test_verify_payment_timeout_raises_timeout_error(mocker, gateway):
    """
    Regression: verification timeouts must be retryable.
    """
    mocker.patch(GET_PATH, side_effect=requests.Timeout())

    with pytest.raises(PaymentGatewayTimeoutError):
        gateway.verify_payment(reference="ref-123")


def test_verify_payment_logs_timeout_error(mocker, caplog, gateway):
    """
    Test timeout error is logged.
    """
    mocker.patch(GET_PATH, side_effect=requests.Timeout())

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME
    ), pytest.raises(PaymentGatewayTimeoutError):
        gateway.verify_payment(reference="ref-123")

    assert "Paystack request timed out" in caplog.text


def test_verify_payment_connection_error_raises_connection_error(
    mocker, gateway
):
    """
    Regression: verification connection failures must be retryable.
    """
    mocker.patch(GET_PATH, side_effect=requests.ConnectionError())

    with pytest.raises(PaymentGatewayConnectionError):
        gateway.verify_payment(reference="ref-123")


def test_verify_payment_logs_connection_error(
    mocker, caplog, gateway
):
    """
    Test that connection failure is logged.
    """
    mocker.patch(GET_PATH, side_effect=requests.ConnectionError())

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME,
    ), pytest.raises(PaymentGatewayConnectionError):
        gateway.verify_payment(reference="ref-123")

    assert "Unable to connect to Paystack" in caplog.text


@pytest.mark.parametrize("status_code", [400, 404, 500, 503])
def test_verify_payment_with_http_error(mocker, gateway, status_code):
    """
    Test that HTTP errors on verification become gateway errors.
    """
    mocker.patch(GET_PATH, return_value=http_error_response(
        mocker, status_code
    ))

    with pytest.raises(PaymentGatewayError):
        gateway.verify_payment(reference="ref-123")


def test_verify_payment_with_false_status(mocker, gateway):
    """
    Test that status=False in the body is surfaced as an error.
    """
    mocker.patch(GET_PATH, return_value=ok_response(mocker, {
        "status": False,
        "message": "Request rejected."
    }))

    with pytest.raises(PaymentGatewayError) as exc_info:
        gateway.verify_payment(reference="ref-123")

    assert exc_info.value.detail == "Request rejected."


def test_verify_payment_logs_false_status_error(caplog, mocker, gateway):
    mocker.patch(GET_PATH, return_value=ok_response(mocker, {
        "status": False,
        "message": "Request rejected."
    }))

    with caplog.at_level(
        logging.INFO,
        logger=PAYSTACK_LOGGER_NAME
    ), pytest.raises(PaymentGatewayError):
        gateway.verify_payment(reference="ref-123")

    assert "Paystack rejected the payment verification" in caplog.text
