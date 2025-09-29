from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from address.models import City
from address.api.v1.serializers import CitySerializer
from address.api.v1.swagger import get_cities_schema
from common.cores.validators import validate_id
from common.utils.api_responses import SuccessAPIResponse


class CityListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(**get_cities_schema)
    def get(self, request):
        """
        Get all cities.
        """
        state_id = request.query_params.get('state')
        validate_id(state_id, 'state')
        cities = City.objects.filter(state__id=state_id)
        serializers = CitySerializer(cities, many=True)
        return Response(SuccessAPIResponse(
            messages="Cities retrieved successfully.",
            data=serializers.data
        ).to_dict(), status=status.HTTP_200_OK)
    