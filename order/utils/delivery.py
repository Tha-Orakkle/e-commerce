from datetime import datetime

from common.exceptions import ErrorException


def calculate_delivery_fee():
    """
    Calculates the delivery fee.
    Temporarily return a fixed amount.
    """
    return 3000.00


def validate_delivery_date(delivery_date):
    """
    Validates the delivery date.
    Ensures it is not in the past.
    """

    if not delivery_date:
        raise ErrorException("Delivery date is required.")
    
    try:
        delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
    except ValueError:
        raise ErrorException("Invalid date format. Use ISO format (YYYY-MM-DD).")
    
    from django.utils.timezone import now
    today = now().date()
    if delivery_date < today:
        raise ErrorException("Delivery date cannot be in the past.")
    return delivery_date