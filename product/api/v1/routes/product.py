from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from common.utils.api_responses import (
    SuccessAPIResponse,
    ErrorAPIResponse
)
from common.utils.pagination import Pagination as PNP
from product.models import Product
from product.serializers.product import ProductSerializer 


class ProductView(APIView):
    def get(self, request):
        """
        Gets all products.
        """
        paginator = PNP()
        queryset = Product.objects.all()
        paginated_queryset  = paginator.paginate_queryset(queryset, request)
        serializers = ProductSerializer(paginated_queryset, many=True, context={'request': request})
        data = paginator.get_paginated_response(serializers.data).data
        return Response(
            SuccessAPIResponse(
                message="Products retrieved successfully.",
                data=data
            ).to_dict(), status=status.HTTP_200_OK
        )


    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                SuccessAPIResponse(
                    message="Product created successfully.",
                    code=201
                ).to_dict(), status=status.HTTP_201_CREATED
            )
        return Response(
            ErrorAPIResponse(
                message="Product creation failed.",
                errors=serializer.errors
            ).to_dict(), status=status.HTTP_400_BAD_REQUEST
        )