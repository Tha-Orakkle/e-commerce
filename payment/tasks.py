from celery import shared_task
from django.conf import settings
from django.db import transaction

import requests

from e_core import logger
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
        payment = Payment.objects.filter(reference=reference).first()
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
                payment.verified = True
                payment.order.is_paid = True
                payment.save(update_fields=['verified'])
                payment.order.save(update_fields=['is_paid'])
            logger.info(f"Payment with reference {reference} verified successfully.")
        else:
            logger.error(f"Payment verification failed for reference {reference}: {res_json.get('message', 'Unknown error')}")
            raise self.retry(exc=Exception(res_json.get('message', 'Payment verification failed')))

    except requests.RequestException as e:
        logger.error(f"Error verifying payment with reference {reference}: {str(e)}")
        raise self.retry(exc=e)
    except Exception as e:
        logger.error(f"Unexpected error verifying payment with reference {reference}: {str(e)}")
        raise self.retry(exc=e)