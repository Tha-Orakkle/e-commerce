from decimal import Decimal
from drf_spectacular.utils import extend_schema
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from cart.utils.validate_cart import validate_cart
from order.models import Order, OrderItem
from order.serializers.order import OrderSerializer
from order.serializers.swagger import checkout_schema
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
        if not validated_response['valid']:
            raise ErrorException(
                "Cart contains invalid items.",
                code=status.HTTP_400_BAD_REQUEST,
            )

        # get shipping/billing address from request body
        # or retrieve the shipping/billing objs with their ids
        # raise appropriate errors for the circumstances
        

        # handle concurrency with atomic transaction
        with transaction.atomic():
            # lock all required inventory up front
            inventory_map = {
                inv.id: inv
                for inv in Inventory.objects.select_for_update()
                .filter(id__in=[item.product.inventory.id for item in cart_items])
            }
            total_amount = Decimal('0.00')
            order_items = []

            # create an order obj
            # to be updated later to accommodate the shipping / address address
            order = Order.objects.create(
                total_amount=total_amount,
                user=request.user
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