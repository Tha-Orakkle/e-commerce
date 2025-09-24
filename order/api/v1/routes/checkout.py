from decimal import Decimal
from drf_spectacular.utils import extend_schema
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from address.models import ShippingAddress
from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from cart.utils.validators import validate_cart
from order.models import Order, OrderItem
from order.serializers.order import OrderSerializer
from order.serializers.swagger import checkout_schema
from order.utils.delivery import calculate_delivery_fee
from product.models import Inventory
from user.models import User


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**checkout_schema)
    def post(self, request):
        """
        Handles the checkout process.
        """
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException("Cart not found.", code=status.HTTP_404_NOT_FOUND)
        cart_items, validated_response = validate_cart(cart)

        if validated_response['items'] == []:
            raise ErrorException("Cart is empty.", code=status.HTTP_400_BAD_REQUEST)
        if not validated_response['is_valid']:
            raise ErrorException(
                "Cart contains invalid items.",
                code=status.HTTP_400_BAD_REQUEST,
            )
        
        shipping_address_id = request.data.get('shipping_address', None)
        validate_id(shipping_address_id, "shipping address")
        shipping_address = ShippingAddress.objects.filter(
            user=request.user, id=shipping_address_id).first()
        if not shipping_address:
            raise ErrorException("Shipping address not found.", code=status.HTTP_404_NOT_FOUND)
        
        fulfillment_method = request.data.get('fulfillment_method')
        payment_method = request.data.get('payment_method')
        if not fulfillment_method or fulfillment_method.strip() not in ['PICKUP', 'DELIVERY']:
            raise ErrorException("Invalid fulfillment method.", code=status.HTTP_400_BAD_REQUEST)
        if not payment_method or payment_method.strip() not in ['CASH', 'DIGITAL']:
            raise ErrorException("Invalid payment method.", code=status.HTTP_400_BAD_REQUEST)


        # handle concurrency with atomic transaction
        with transaction.atomic():
            # lock all required inventory up front
            inventory_map = {
                inv.id: inv
                for inv in Inventory.objects.select_for_update()
                .filter(id__in=[item.product.inventory.id for item in cart_items])
            }
            total_amount = Decimal(calculate_delivery_fee()) if fulfillment_method.strip() == 'DELIVERY' else Decimal('0.00')
            order_items = []

            # create an order obj
            order = Order.objects.create(
                total_amount=Decimal('0.00'),
                shipping_address=shipping_address,
                user=request.user,
                fulfillment_method=fulfillment_method.strip(),
                payment_method=payment_method.strip()
            )

            for item in cart_items:
                inventory = inventory_map[item.product.inventory.id]
                if item.quantity > inventory.stock:
                    raise ErrorException(
                        f"Insufficient stock for {item.product.name}. Only {inventory.stock} left.",
                        code=status.HTTP_400_BAD_REQUEST
                    )
                
                total_amount += item.quantity * item.product.price
                inventory.stock -= item.quantity
                inventory.save()
                order_items.append(OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                ))
            
            order.total_amount = total_amount
            order.save()
            OrderItem.objects.bulk_create(order_items)
            cart_items.delete()
        
        serializer = OrderSerializer(order)
        return Response(SuccessAPIResponse(
            message="Checkout successful. Order has been created.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)
