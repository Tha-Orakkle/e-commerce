from decimal import Decimal
from typing import Any



class PaystackGateway:
    BASE_URL = "https://api.paystack.co"
    
    def initialize_payment(
        self,
        *,
        reference: str,
        amount: Decimal,
        currency: str,
        customer_email: str,
        metadata: dict[str, Any]
    ):
        """
        Initialize payment and get authorization url.
        """
        pass
        
        
        