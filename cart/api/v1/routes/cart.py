from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.cores.validators import validate_id
from common.permissions import IsCustomer
from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from product.models import Product
from cart.api.v1.serializers import CartSerializer, CartItemSerializer
from cart.api.v1.swagger import (
    add_to_cart_schema,
    get_cart_schema,
    update_cart_schema,
)
from cart.utils.validators import validate_cart

User = get_user_model()


class CartDetailView(APIView):
    permission_classes = [IsCustomer]

    @extend_schema(**add_to_cart_schema)
    def post(self, request):
        """
        Adds an item to the cart.
        """
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException(
                detail="No cart found for the user.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
            
        product_id = request.data.get('product')
        validate_id(product_id, "product")
        product = Product.objects.select_related('inventory').filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="No product found with the given ID.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        quantity = request.data.get('quantity', 1)
        try:
            quantity = int(quantity)
        except:
            raise ErrorException(
                detail="Provide a valid quantity that is greater than 0.",
                code='invalid_quantity'    
            )
        if quantity < 1:
            raise ErrorException(
                detail="Provide a valid quantity that is greater than 0.",
                code='invalid_quantity'
            )
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
            raise ErrorException(
                detail="No cart found for the user.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        return Response(SuccessAPIResponse(
            message='Cart retrieved successfully.',
            data=validated_response
        ).to_dict(), status=status.HTTP_200_OK)


class CartItemDetailView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request, cart_item_id):
        """
        Gets a specific item in the cart.
        """
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException(
                detail="No cart found for the user.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        validate_id(cart_item_id, "cart item")
        item = cart.items.filter(id=cart_item_id).first()
        if not item:
            raise ErrorException(
                detail="No item matching given ID found in cart.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        return Response(SuccessAPIResponse(
            message="Cart item retrieved successfully.",
            data=CartItemSerializer(item).data
        ).to_dict(), status=status.HTTP_200_OK)

 
    @extend_schema(**update_cart_schema)
    def post(self, request, cart_item_id):
        """
        Updates quantity of an item already on the Cart.
        """
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException(
                detail="No cart found for the user.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        validate_id(cart_item_id, "cart item")
        item = cart.items.select_related('product__inventory').filter(id=cart_item_id).first()
        if not item:
            raise ErrorException(
                detail="No item matching given ID found in cart.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )

        operation = request.data.get('operation')
        if operation == 'increment':
            cart = cart.increment_item_quantity(item)
        elif operation == 'decrement':
            cart = cart.decrement_item_quantity(item)
        else:
            raise ErrorException(
                detail="Provide a valid operation: 'increment' or 'decrement'.",
                code='invalid_operation'
            )
        
        return Response(SuccessAPIResponse(
            message="Cart item updated successfully.",
            data=CartItemSerializer(item).data
        ).to_dict(), status=status.HTTP_200_OK)


    def delete(self, request, cart_item_id):
        """
        Deletes an item from the cart.
        """
        validate_id(cart_item_id, "cart item")
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException(
                detail="No cart found for the user.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        item = cart.items.filter(id=cart_item_id).first()
        if not item:
            raise ErrorException(
                detail="No item matching given ID found in cart.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        cart = cart.remove_from_cart(item)
        return Response({}, status=status.HTTP_204_NO_CONTENT)