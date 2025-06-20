from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from address.serializers.shipping_address import ShippingAddressSerializer
from address.serializers.swagger import (
    create_shipping_address_schema,
    delete_shipping_address_schema,
    get_shipping_addresses_schema,
    get_shipping_address_schema,
    update_shipping_address_schema
)
from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.check_valid_uuid import validate_id


class ShippingAddressView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_shipping_addresses_schema)
    def get(self, request):
        """
        Get a specific user's shipping addresses.
        """
        addresses = request.user.addresses.all()
        serializers = ShippingAddressSerializer(addresses, many=True)
        return Response(SuccessAPIResponse(
            message="Shipping addresses retrieved successfully.",
            data=serializers.data
        ).to_dict(), status=status.HTTP_200_OK)
    
    @extend_schema(**create_shipping_address_schema)
    def post(self, request):
        """
        Create a new ShippingAddress instance.
        """
        serializer = ShippingAddressSerializer(data=request.data)
        if not serializer.is_valid():
            raise ErrorException(
                detail="Shipping address creation failed.",
                errors=serializer.errors
            )
        serializer.save(user=request.user)
        return Response(SuccessAPIResponse(
            message="Shipping address created succssfully.",
            code=201,
            data=serializer.data
        ).to_dict(), status=status.HTTP_201_CREATED)
    

class ShippingAddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_shipping_address_schema)
    def get(self, request, address_id):
        """
        Get a specific shipping address by ID.
        """
        validate_id(address_id, "shipping address")
        address = request.user.addresses.filter(id=address_id).first()
        if not address:
            raise ErrorException("Shipping address not found.", code=status.HTTP_404_NOT_FOUND)
        
        serializer = ShippingAddressSerializer(address)
        return Response(SuccessAPIResponse(
            message="Shipping address retrieved successfully.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)
    
    @extend_schema(**update_shipping_address_schema)
    def put(self, request, address_id):
        """
        Update a specific shipping address by ID.
        """
        validate_id(address_id, "shipping address")
        address = request.user.addresses.filter(id=address_id).first()
        if not address:
            raise ErrorException(detail="Shipping address not found.", code=status.HTTP_404_NOT_FOUND)
        
        serializer = ShippingAddressSerializer(
            instance=address,
            data=request.data,
            partial=True
        )
        if not serializer.is_valid():
            raise ErrorException(
                detail="Shipping address update failed.",
                errors=serializer.errors
            )
        
        serializer.save(user=request.user)
        return Response(SuccessAPIResponse(
            message="Shipping address updated successfully.",
            data=serializer.data
        ).to_dict(), status=status.HTTP_200_OK)


    @extend_schema(**delete_shipping_address_schema)
    def delete(self, request, address_id):
        """
        Delete a specific shipping address by ID.
        """
        validate_id(address_id, "shipping address")
        address = request.user.addresses.filter(id=address_id).first()
        if not address:
            raise ErrorException(detail="Shipping address not found.", code=status.HTTP_404_NOT_FOUND)
        
        address.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
