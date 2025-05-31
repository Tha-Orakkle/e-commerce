from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status

from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from product.models import Product
from product.serializers.inventory import InventorySerializer

class InventoryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, product_id):
        """
        Updates the quantity of a product in the inventory
        """
        validate_id(product_id, 'product')

        product = Product.objects.select_related('inventory').filter(id=product_id).first()
        if not product:
            raise ErrorException("Product not found.", code=status.HTTP_404_NOT_FOUND)
        
        action = request.GET.get('action')
        quantity = request.data.get('quantity')
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ErrorException("Provide a valid quantity that is greater than 0.")
        inventory = None
        if action == 'add':
            inventory = product.inventory.add(quantity, request.user.staff_id)
        elif action == 'subtract':
            inventory = product.inventory.substract(quantity, request.user.staff_id)
        else:
            raise ErrorException("Invalid action")
        return Response(SuccessAPIResponse(
            message=f"Inventory updated successfully.",
            data=InventorySerializer(inventory).data
        ).to_dict(), status=status.HTTP_200_OK)
