from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from address.models import ShippingAddress
from address.api.v1.serializers import (
    ShippingAddressSerializer,
    ShippingAddressCreateUpdateSerializer
)
from address.api.v1.swagger import (
    post_shipping_address_schema,
    delete_shipping_address_schema,
    get_shipping_addresses_schema,
    get_shipping_address_schema,
    patch_shipping_address_schema
)
from common.cores.validators import validate_id
from common.exceptions import ErrorException
from common.permissions import IsCustomer
from common.utils.api_responses import SuccessAPIResponse


class ShippingAddressListCreateView(APIView):
    permission_classes = [IsCustomer]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ShippingAddress.objects.all()
        
        return user.addresses.all()

    @extend_schema(**get_shipping_addresses_schema)
    def get(self, request):
        """
        Get a specific user's shipping addresses.
        """
        qs = self.get_queryset()
        serializers = ShippingAddressSerializer(qs, many=True, context={'request': request})
        return Response(SuccessAPIResponse(
            message="Shipping addresses retrieved successfully.",
            data=serializers.data
        ).to_dict(), status=status.HTTP_200_OK)


    @extend_schema(**post_shipping_address_schema)
    def post(self, request):
        """
        Create a new ShippingAddress instance.
        """
        serializer = ShippingAddressCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            address = serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Shipping address creation failed.",
                code='validation_error',
                errors=e.detail
            )
        return Response(SuccessAPIResponse(
            message="Shipping address created succssfully.",
            data=ShippingAddressSerializer(address).data
        ).to_dict(), status=status.HTTP_201_CREATED)
    

class ShippingAddressDetailView(APIView):
    permission_classes = [IsCustomer]

    def get_object(self, address_id):
        user = self.request.user
        if user.is_superuser:
            return ShippingAddress.objects.filter(id=address_id).first()

        return user.addresses.filter(id=address_id).first()

    @extend_schema(**get_shipping_address_schema)
    def get(self, request, address_id):
        """
        Get a specific shipping address by ID.
        """
        validate_id(address_id, "shipping address")
        address = self.get_object(address_id)
        if not address:
            raise ErrorException(
                detail="No shipping address matching the given ID found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        
        return Response(SuccessAPIResponse(
            message="Shipping address retrieved successfully.",
            data=ShippingAddressSerializer(address, context={'request': request}).data
        ).to_dict(), status=status.HTTP_200_OK)
    
    @extend_schema(**patch_shipping_address_schema)
    def patch(self, request, address_id):
        """
        Update a specific shipping address by ID.
        """
        validate_id(address_id, "shipping address")
        address = self.get_object(address_id)
        if not address:
            raise ErrorException(
                detail="No shipping address matching given ID found.", 
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)

        serializer = ShippingAddressCreateUpdateSerializer(
            instance=address,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            address = serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail="Shipping address update failed.",
                code='validation_error',
                errors=serializer.errors
            )
        return Response(SuccessAPIResponse(
            message="Shipping address updated successfully.",
            data=ShippingAddressSerializer(address).data
        ).to_dict(), status=status.HTTP_200_OK)


    @extend_schema(**delete_shipping_address_schema)
    def delete(self, request, address_id):
        """
        Delete a specific shipping address by ID.
        """
        validate_id(address_id, "shipping address")
        address = self.get_object(address_id)
        if not address:
            raise ErrorException(
                detail="Shipping address not found.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)

        address.delete()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
