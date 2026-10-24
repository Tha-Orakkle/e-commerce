import uuid
from decimal import Decimal

from payment.tasks import verify_payment_task

SERVICE_PATH = "payment.tasks.get_payment_verification_service"


def test_task_ignores_empty_reference(mocker):
    """
    Test that a missing reference is dropped without verifying.
    """
    get_service = mocker.patch(SERVICE_PATH)

    assert verify_payment_task("") is None

    get_service.assert_not_called()


def test_task_ignores_unknown_reference(db, mocker):
    """
    Test that a reference with no transaction is dropped quietly.
    """
    get_service = mocker.patch(SERVICE_PATH)

    assert verify_payment_task(str(uuid.uuid4())) is None

    get_service.assert_not_called()


def test_task_verifies_the_matching_transaction(
    mocker, customer, order_group_factory, payment_factory,
    payment_transaction_factory
):
    """
    Test that the task looks the transaction up by reference and hands
    its id to the verification service.
    """
    group = order_group_factory(
        user=customer, total_amount=Decimal("1000.00")
    )
    payment = payment_factory(group)
    tx = payment_transaction_factory(payment, active=True)
    service = mocker.Mock()
    mocker.patch(SERVICE_PATH, return_value=service)

    verify_payment_task(str(tx.reference))

    service.verify.assert_called_once_with(transaction_id=tx.id)
