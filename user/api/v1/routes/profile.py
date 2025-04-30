from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils.api_responses import (
    SuccessAPIResponse,
    ErrorAPIResponse
)
from user.models import User
from user.serializers.profile import UserProfileSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        """
        Update the user profile.
        """
        user = request.user
        try:
            user.profile
        except User.profile.RelatedObjectDoesNotExist:
            return Response(
                ErrorAPIResponse(
                    message="User has no profile.",
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UserProfileSerializer(user.profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                ErrorAPIResponse(
                    message="Error updating user profile.",
                    errors=serializer.errors,
                ).to_dict(), status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(
            SuccessAPIResponse(
                message="User profile updated successfully.",
                data=serializer.data,
            ).to_dict(), status=status.HTTP_200_OK
        )
