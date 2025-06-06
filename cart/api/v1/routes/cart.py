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
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        try:
            quantity = int(quantity)
        except:
            raise ErrorException("Provide a valid quantity that is greater than 0.")
        if quantity < 1:
            raise ErrorException("Provide a valid quantity that is greater than 0.")
        validate_id(product_id, "product")
        product = Product.objects.filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        cart = cart.add_item(product, quantity)
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
            validated_response = validate_cart(cart)
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException("Cart not found.", code=status.HTTP_404_NOT_FOUND)
        return Response(SuccessAPIResponse(
            message='Cart retrieved successfully.',
            data= validated_response
        ).to_dict(), status=status.HTTP_200_OK)


class UpdateCartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**update_cart_schema)
    def post(self, request, product_id):
        """
        Updates quantity of an item already on the Cart.
        """
        validate_id(product_id, "product")
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException("Cart not found.", code=status.HTTP_404_NOT_FOUND)


        item = cart.items.select_related('product').filter(product__id=product_id).first()
        if not item:
            raise ErrorException("Product not found in cart.", code=status.HTTP_404_NOT_FOUND)

        action = request.query_params.get('action')
        quantity = request.data.get('quantity', 1)

        if action == 'add':
            cart = cart.add_items(item.product, quantity)
        elif action == 'remove':
            cart = cart.remove_item(item, quantity)
        else:
            raise ErrorException("Invalid action.")
        return Response(SuccessAPIResponse(
            message="Cart item updated successfully.",
            data=CartSerializer(cart).data
        ).to_dict(), status=status.HTTP_200_OK)
