from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from address.models import ShippingAddress
from cart.utils.validators import validate_cart
from common.cores.validators import validate_id
from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from order.api.v1.serializers import OrderGroupSerializer
from order.serializers.swagger import checkout_schema
from order.utils.orders import create_orders_from_cart


User = get_user_model()


class CheckoutView(APIView):
    permission_classes = [IsCustomer]
    
    @extend_schema(**checkout_schema)
    def post(self, request):
        """
        Handles the checkout process.
        """
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException(
                detail="No cart found for the user.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        cart_items, validated_response = validate_cart(cart, include_shop=True)
        if validated_response['items'] == []:
            raise ErrorException(
                detail="Cart is empty.",
                code='empty_cart'
            )
        if not validated_response['is_valid']:
            raise ErrorException(
                detail="Cart contains invalid items.",
                code='invalid_cart',
            )


        errors = {}
        
        # shipping address
        ship_add_id = request.data.get('shipping_address', None)
        if not ship_add_id:
            errors.setdefault('shipping_address', []).append('This field is required.')
        else:
            try:
                valid = validate_id(ship_add_id, "shipping address")
            except ErrorException as e:
                errors.setdefault('shipping_address', []).append(e.detail) 
            if valid:
                ship_add = ShippingAddress.objects.select_related(
                    'city__state__country'
                ).filter(user=request.user, id=ship_add_id).first()
                if not ship_add:
                    errors.setdefault('shipping_address', []).append(
                        "No shipping address matching the given ID found.")
        
        # fulfullment method
        fulfillment_method = request.data.get('fulfillment_method', '').upper().strip()
        if not fulfillment_method or fulfillment_method not in ['PICKUP', 'DELIVERY']:
            errors.setdefault('fulfillment_method', []).append(
                "The fulfillment method must be either 'PICKUP' or 'DELIVERY'.")

        # payment method
        payment_method = request.data.get('payment_method', '').upper().strip()
        if not payment_method or payment_method not in ['CASH', 'DIGITAL']:
            errors.setdefault('payment_method', []).append(
                "The payment method must be either 'CASH' or 'DIGITAL'.")
            
        if errors:
            raise ErrorException(
                detail="Invalid request data.",
                code='missing_or_invalid_fields',
                errors=errors
            )
            
        order_group = create_orders_from_cart(
            user=request.user,
            shipping_address=ship_add,
            fulfillment_method=fulfillment_method,
            payment_method=payment_method,
            cart_items=cart_items
        )
        
        return Response(SuccessAPIResponse(
            message="Checkout successful. Orders have been created.",
            data=OrderGroupSerializer(order_group).data
        ).to_dict(), status=status.HTTP_200_OK)
