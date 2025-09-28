from datetime import datetime

from common.exceptions import ErrorException


def validate_delivery_date(delivery_date):
    """
    Validates the delivery date.
    Ensures it is not in the past.
    """

    if not delivery_date:
        raise ErrorException(
            detail="Delivery date is required for 'DELIVERY' orders ready to be shipped.",
            code='missing_field'
        )
    try:
        delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
    except ValueError:
        raise ErrorException(
            detail="Invalid date format. Use ISO format (YYYY-MM-DD).",
            code='invalid_date_format'
        )
    
    from django.utils.timezone import now
    today = now().date()
    if delivery_date < today:
        raise ErrorException(
            detail="Delivery date cannot be in the past.",
            code='invalid_delivery_date'
        )
    return delivery_date


def validate_order(status, order, group, payment_status=False):
    """
    Validates the order status and checks if it can be updated.
    """
    
    if status == 'PROCESSING':
        if order.status not in ['PENDING', 'PROCESSING']:
            raise ErrorException(
                detail=f"Order must be a pending order. Current status is {order.status}.",
                code='invalid_status_transition'
            )
        if group.payment_method == 'DIGITAL' and not group.is_paid:
            raise ErrorException(
                detail="Non-cash orders must be paid before processing order.",
                code='invalid_status_transition'
            )
    elif status == 'SHIPPED':
        if group.fulfillment_method == 'PICKUP':
            raise ErrorException(
                detail="Pickup orders cannot be shipped.",
                code='invalid_status_transition'
            )
        if order.status not in  ['PROCESSING', 'SHIPPED']:
            raise ErrorException(
                detail=f"Order must be a processing order. Current status is {order.status}.",
                code='invalid_status_transition'
            )
        if group.payment_method == 'DIGITAL' and not group.is_paid:
            raise ErrorException(
                detail="Non-cash orders must be paid before shipping order.",
                code='invalid_payment_status'
            )
    
    elif status == 'COMPLETED':
        if group.fulfillment_method == 'DELIVERY' and order.status not in ['SHIPPED', 'COMPLETED']:
            raise ErrorException(
                detail=f"Order must be a shipped order. Current status is {order.status}.",
                code='invalid_status_transition'
            )
        elif group.fulfillment_method == 'PICKUP' and order.status not in ['PROCESSING', 'COMPLETED']:
            raise ErrorException(
                detail=f"Order must be a processing order. Current status is {order.status}.",
                code='invalid_status_transition'
            )

        if group.payment_method == 'DIGITAL' and not group.is_paid:
            raise ErrorException(
                detail="Non-cash orders must be paid before completing order.",
                code='invalid_status_transition'
            )
        elif group.payment_method =='CASH' and not group.is_paid and not payment_status:
            raise ErrorException(
                detail='Cash orders must be paid before completing order. Please provide payment status.',
                code='invalid_payment_status'
            )
    elif status == 'CANCELLED':
        if order.status not in ['PENDING', 'PROCESSING']:
            raise ErrorException(
                detail=f"Order must be a pending or processing order. Current status is {order.status}.",
                code='invalid_status_transition'
            )
    else:
        raise ErrorException(
            detail="Invalid status provided.",
            code='invalid_status'
        )
    return True
