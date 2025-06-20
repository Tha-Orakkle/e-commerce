from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from address.models import State
from address.serializers.state import StateSerializer
from address.serializers.swagger import get_states_schema
from common.utils.api_responses import SuccessAPIResponse


class StateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**get_states_schema)
    def get(self, request):
        """
        Get a list of all states in a country.
        """
        country_code = request.query_params.get('country')
        states = State.objects.filter(country__code=country_code)
        serializers = StateSerializer(states, many=True)
        return Response(SuccessAPIResponse(
            message="States retrieved successfully.",
            data=serializers.data
        ).to_dict(), status=status.HTTP_200_OK)
