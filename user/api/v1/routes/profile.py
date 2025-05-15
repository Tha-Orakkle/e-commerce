from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from user.models import User
from user.serializers.profile import UserProfileSerializer
from user.serializers.swagger import update_user_profile_schema

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(**update_user_profile_schema)
    def put(self, request):
        """
        Update the user profile.
        """
        user = request.user
        try:
            user.profile
        except User.profile.RelatedObjectDoesNotExist:
            raise ErrorException("User has no profile.")
        serializer = UserProfileSerializer(user.profile, data=request.data, partial=True)
        if not serializer.is_valid():
            raise ErrorException(
                detail="User profile update failed.",
                errors=serializer.errors    
            )
        serializer.save()
        return Response(
            SuccessAPIResponse(
                message="User profile updated successfully.",
                data=serializer.data,
            ).to_dict(), status=status.HTTP_200_OK
        )
