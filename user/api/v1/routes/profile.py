from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from user.models import User
from user.serializers.profile import UserProfileSerializer
from user.serializers.swagger import update_user_profile_schema, user_profile_category_add_or_remove_schema

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
            raise ErrorException("User has no profile.", code=status.HTTP_404_NOT_FOUND)
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


class UserProfileCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(**user_profile_category_add_or_remove_schema)
    def post(self, request):
        """
        Add category to your preferences. This will be used for
        product recommendation.
        """
        try:
            profile = request.user.profile
        except User.profile.RelatedObjectDoesNotExist:
            raise ErrorException("User has no profile.", code=status.HTTP_404_NOT_FOUND)
        action = request.query_params.get('action')
        categories = request.data.getlist('categories', [])
        if action == 'add':
            profile.add_categories(categories)
        elif action == 'remove':
            profile.remove_categories(categories)
        else:
            raise ErrorException(detail="Invalid action.", code=status.HTTP_400_BAD_REQUEST)
        return Response(SuccessAPIResponse(
            message='User preferred categories updated.'
        ).to_dict(), status=status.HTTP_200_OK)
