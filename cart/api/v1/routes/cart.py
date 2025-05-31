from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from product.models import Product
from cart.serializers.cart import CartSerializer



class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Adds an item to the cart.
        """
        cart = request.user.cart
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
    
