from datetime import timedelta

import pytest
from django.utils import timezone

from order.models import OrderOutboxEventStatus
from order.tasks import dispatch_order_outbox_events


@pytest.mark.django_db
def test_dispatch_outbox_event_publishes_restock_task(
    order_outbox_event,
    mocker,
):
    publish = mocker.patch(
        "order.tasks.restock_inventory_with_cancelled_order.apply_async"
    )

    result = dispatch_order_outbox_events()

    order_outbox_event.refresh_from_db()

    assert result["published"] == 1
    assert order_outbox_event.status == OrderOutboxEventStatus.PUBLISHED
    assert order_outbox_event.published_at is not None
    assert order_outbox_event.attempts == 0
    publish.assert_called_once()


@pytest.mark.django_db
def test_dispatch_failure_keeps_event_pending(
    order_outbox_event,
    mocker,
):
    mocker.patch(
        "order.tasks.restock_inventory_with_cancelled_order.apply_async",
        side_effect=ConnectionError("Broker unavailable"),
    )

    before = timezone.now()

    result = dispatch_order_outbox_events()

    order_outbox_event.refresh_from_db()

    assert result["failed"] == 1
    assert order_outbox_event.status == OrderOutboxEventStatus.PENDING
    assert order_outbox_event.attempts == 1
    assert order_outbox_event.last_error
    assert order_outbox_event.next_attempt_at > before
    assert order_outbox_event.published_at is None


@pytest.mark.django_db
def test_dispatch_ignores_published_events(
    published_order_outbox_event,
    mocker,
):
    publish = mocker.patch(
        "order.tasks.restock_inventory_with_cancelled_order.apply_async"
    )

    result = dispatch_order_outbox_events()

    assert result["published"] == 0
    publish.assert_not_called()


@pytest.mark.django_db
def test_dispatch_ignores_events_not_yet_due(
    order_outbox_event,
    mocker,
):
    order_outbox_event.next_attempt_at = timezone.now() + timedelta(hours=1)
    order_outbox_event.save(update_fields=["next_attempt_at"])

    publish = mocker.patch(
        "order.tasks.restock_inventory_with_cancelled_order.apply_async"
    )

    result = dispatch_order_outbox_events()

    assert result["published"] == 0
    publish.assert_not_called()
