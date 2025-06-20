from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from address.models import Country
from address.serializers.country import CountrySerializer
from address.serializers.swagger import get_countries_schema
from common.utils.api_responses import SuccessAPIResponse


class CountryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_countries_schema)
    def get(self, request):
        """
        Get a liat of all supported countries.
        """
        countries = Country.objects.all()
        serializers = CountrySerializer(countries, many=True)
        return Response(SuccessAPIResponse(
            message="Countries retreived successfully.",
            data=serializers.data
        ).to_dict(), status=status.HTTP_200_OK)
