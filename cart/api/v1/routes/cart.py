from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from product.models import Product
from cart.serializers.cart import CartSerializer
from cart.serializers.swagger import (
    add_to_cart_schema,
    get_cart_schema,
    update_cart_schema,
)
from cart.utils.validate_cart import validate_cart


User = get_user_model()

class CartView(APIView):
    permission_classes = [IsAuthenticated]


    @extend_schema(**add_to_cart_schema)
    def post(self, request):
        """
        Adds an item to the cart.
        """
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException("Cart not found.", code=status.HTTP_404_NOT_FOUND)
        product_id = request.data.get('product')
        quantity = request.data.get('quantity', 1)
        try:
            quantity = int(quantity)
        except:
            raise ErrorException("Provide a valid quantity that is greater than 0.")
        if quantity < 1:
            raise ErrorException("Provide a valid quantity that is greater than 0.")
        validate_id(product_id, "product")
        product = Product.objects.select_related('inventory').filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        cart = cart.add_to_cart(product, quantity)
        serializer = CartSerializer(cart)
        return Response(SuccessAPIResponse(
            message="Item added to cart successfully.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)
    

    @extend_schema(**get_cart_schema)
    def get(self, request):
        """
        Get the cart and all items.
        """
        validated_response = None
        try:
            cart = request.user.cart
            _, validated_response = validate_cart(cart)
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException("Cart not found.", code=status.HTTP_404_NOT_FOUND)
        return Response(SuccessAPIResponse(
            message='Cart retrieved successfully.',
            data= validated_response
        ).to_dict(), status=status.HTTP_200_OK)


class UpdateCartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**update_cart_schema)
    def post(self, request, cart_item_id):
        """
        Updates quantity of an item already on the Cart.
        """
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException("Cart not found.", code=status.HTTP_404_NOT_FOUND)

        validate_id(cart_item_id, "cart item")
        item = cart.items.select_related('product__inventory').filter(id=cart_item_id).first()
        if not item:
            raise ErrorException("Item not found in cart.", code=status.HTTP_404_NOT_FOUND)


        operation = request.data.get('operation')
        if operation == 'increment':
            cart = cart.increment_item_quantity(item)
        elif operation == 'decrement':
            cart = cart.decrement_item_quantity(item)
        else:
            raise ErrorException("Invalid operation.")
        
        return Response(SuccessAPIResponse(
            message="Cart item updated successfully.",
            data=CartSerializer(cart).data
        ).to_dict(), status=status.HTTP_200_OK)
