from common.exceptions import ErrorException
from order.models import Order

def validate_order(status, order, payment_status=False):
    """
    Validates the order status and checks if it can be updated.
    """
    statuses = list(dict(Order.ORDER_STATUS_CHOICES))
    
    if status == 'PROCESSING':
        if order.status not in ['PENDING', 'PROCESSING']:
            raise ErrorException(f"Order must be a pending order. Current status is {order.status}.")
        if order.payment_method == 'DIGITAL' and not order.is_paid:
            raise ErrorException("Non-cash orders must be paid before processing order.")
            
    elif status == 'SHIPPED':
        if order.fulfillment_method == 'PICKUP':
            raise ErrorException("Pickup orders cannot be shipped.")
        if order.status not in  ['PROCESSING', 'SHIPPED']:
            raise ErrorException(f"Order must be a processing order. Current status is {order.status}.")
        if order.payment_method == 'DIGITAL' and not order.is_paid:
            raise ErrorException("Non-cash orders must be paid before shipping order.")
    
    elif status == 'COMPLETED':
        if order.fulfillment_method == 'DELIVERY' and order.status not in ['SHIPPED', 'COMPLETED']:
            raise ErrorException(f"Order must be a shipped order. Current status is {order.status}.")
        elif order.fulfillment_method == 'PICKUP' and order.status not in ['PROCESSING', 'COMPLETED']:
            raise ErrorException(f"Order must be a processing order. Current status is {order.status}.")
        
        if order.payment_method == 'DIGITAL' and not order.is_paid:
            raise ErrorException("Non-cash orders must be paid before completing order.")
        elif order.payment_method =='CASH' and not order.is_paid and not payment_status:
            raise ErrorException('Cash orders must be paid before completing order. Please provide payment status.')
    elif status == 'CANCELLED':
        if order.status not in ['PENDING', 'PROCESSING', 'CANCELLED']:
            raise ErrorException(f"Order must be a pending or processing order. Current status is {order.status}.")
    else:
        raise ErrorException("Invalid status provided.")