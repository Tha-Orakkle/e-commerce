from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from common.exceptions import ErrorException
from common.permissions import IsStaff
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id
from product.models import Product
from product.api.v1.serializers import InventorySerializer
from product.serializers.swagger import update_inventory_schema

class InventoryView(APIView):
    permission_classes = [IsStaff]

    @extend_schema(**update_inventory_schema)
    def post(self, request, product_id):
        """
        Updates the quantity of a product in the inventory
        """
        validate_id(product_id, 'product')

        product = Product.objects.select_related('inventory').filter(id=product_id).first()
        if not product:
            raise ErrorException(
                detail="Product not found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
            
        if not request.user.can_manage_product(product):
            raise PermissionDenied()
        
        action = request.data.get('action')
        quantity = request.data.get('quantity')
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ErrorException(
                detail="Provide a valid quantity that is greater than 0.",
                code='invalid_quantity'
            )
        inventory = None
        if action not in ['add', 'subtract']:
            raise ErrorException(
                detail="Provide a valid action: 'add' or 'subtract'.",
                code='invalid_action')
        try:
            if action == 'add':
                inventory = product.inventory.add(quantity, request.user.staff_id)
            elif action == 'subtract':
                inventory = product.inventory.substract(quantity, request.user.staff_id)
        except ValueError as ve:
            raise ErrorException(
                detail=str(ve),
                code='invalid_quantity'
            )
        except ErrorException as ee:
            raise ee

        return Response(SuccessAPIResponse(
            message=f"Inventory updated successfully.",
            data=InventorySerializer(inventory).data
        ).to_dict(), status=status.HTTP_200_OK)
