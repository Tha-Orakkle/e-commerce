from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

import requests

from e_core import logger
from order.models import Order
from payment.models import Payment

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def verify_paystack_payment(self, data):
    """
    Celery task to verify Paystack payment.
    This task can be used to verify payments in the background.
    """
    if not data or not data.get('reference'):
        logger.error("Missing payment reference in Paystack webhook data.")
        return
    reference = data['reference']

    try:
        payment = Payment.objects.select_related('order_group').filter(reference=reference).first()
        if not payment:
            logger.error(f"Payment with reference {reference} not found.")
            return
        if payment.verified:
            logger.info(f"Payment with reference {reference} is already verified.")
            return
        
        verify_url = f"{settings.PAYSTACK_VERIFY_URL}{reference}"
        headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
        res = requests.get(verify_url, headers=headers)
        res_json = res.json()
        
        if res.status_code == 200 and res_json['data']['status'] == 'success':
            with transaction.atomic():
                _now = now()
                paid_at = res_json.get('paid_at', None)
                if paid_at:
                    _now = now().fromisoformat(paid_at)
                    
                payment.paid_at = _now
                payment.verified = True
                orders = list(payment.order_group.orders.all())
                for order in orders:
                    order.is_paid = True
                    order.paid_at = _now
                Order.objects.bulk_update(orders, ['is_paid', 'paid_at'])
                payment.save(update_fields=['paid_at', 'verified'])

            logger.info(f"Payment with reference {reference} verified successfully.")
        else:
            logger.error(f"Payment verification failed for reference {reference}: {res_json.get('message', 'Paystack error')}")
            raise self.retry(exc=Exception(res_json.get('message', 'Payment verification failed')))

    except requests.RequestException as e:
        logger.error(f"Error verifying payment with reference {reference}: {str(e)}")
        raise self.retry(exc=e)
    except Exception as e:
        logger.error(f"Unexpected error verifying payment with reference {reference}: {str(e)}")
        raise self.retry(exc=e)