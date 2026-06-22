from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


from cart.utils.validators import validate_cart
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from common.utils.api_responses import SuccessAPIResponse
from order.api.v1.serializers import CheckoutSerializer, OrderGroupSerializer
from order.domain.exceptions import EmptyCartError, InvalidCartError
from order.services import CheckoutService


User = get_user_model()

class CheckoutView(APIView):
    """
    Endpoint for checking out. 
    Creates order from the items in the cart.
    """
    permission_classes = [IsCustomer]
    
    def post(self, request):
        try:
            cart = request.user.cart
        except User.cart.RelatedObjectDoesNotExist:
            raise ErrorException(
                detail="No cart found for the user.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # validate input
        serializer = CheckoutSerializer(
            data=request.data, context={"request": request})

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            raise ErrorException(
                detail="Checkout failed. Invalid request data.",
                code="validation_error",
                errors=serializer.errors
            )
            
        # validate cart items
        cart_items = cart.items.select_related(
            "product__inventory", "product__shop"
        )
        validated = validate_cart(cart_items)
        # cart_items, validated = validate_cart(cart, include_shop=True)
        if not validated["is_valid"]:
            raise ErrorException(
                detail="Cart contains invalid items.",
                code="invalid_cart",
                errors=[item for item in validated["items"]
                        if item["status"] != "available"]
            )
        
        service = CheckoutService(
            user=request.user,
            cart=cart,
            cart_items=cart_items,
            shipping_address=serializer.validated_data["shipping_address"],
            payment_method=serializer.validated_data["payment_method"],
            fulfillment_method=serializer.validated_data["fulfillment_method"],
        )
        try:
            order_group = service.execute()
        except EmptyCartError:
            raise ErrorException(
               detail="Cart is empty.",
                code="empty_cart"
            )
        except InvalidCartError as e:
            raise ErrorException(
                detail="Cart contains invalid items.",
                code='invalid_cart',
                errors=e.errors
            )
        
        return Response(SuccessAPIResponse(
            message="Checkout successful. Orders have been created.",
            data=OrderGroupSerializer(order_group).data
        ).to_dict(), status=status.HTTP_201_CREATED)
        