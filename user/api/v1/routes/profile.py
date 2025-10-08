from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from common.permissions import IsCustomer
from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from user.models import User
from user.api.v1.serializers import UserProfileSerializer
from user.api.v1.swagger import (
    update_user_profile_schema,
    update_user_preferred_category_schema
)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(**update_user_profile_schema)
    def patch(self, request):
        """
        Update the user profile.
        """
        user = request.user
        try:
            user.profile
        except User.profile.RelatedObjectDoesNotExist:
            raise ErrorException(
                detail="User has no profile.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileSerializer(user.profile, data=request.data, partial=True)
        if not serializer.is_valid():
            raise ErrorException(
                detail="User profile update failed.",
                code='validation_error',
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
    permission_classes = [IsCustomer]

    @extend_schema(**update_user_preferred_category_schema)
    def post(self, request):
        """
        Add category to your preferences. This will be used for
        product recommendation.
        """
        try:
            profile = request.user.profile
        except User.profile.RelatedObjectDoesNotExist:
            raise ErrorException(
                detail="User has no profile.",
                code='not_found',
                status_code=status.HTTP_404_NOT_FOUND)
        action = request.data.get('action', '')
        if 'categories' not in request.data:
            raise ErrorException(
                detail="Please provide a list of categories in the 'categories' field.",
                code='missing_categories'
            )

        categories = request.data.getlist('categories', [])
        if action == 'add':
            profile.add_categories(categories)
        elif action == 'remove':
            profile.remove_categories(categories)
        else:
            raise ErrorException(
                detail="Enter a valid action: 'add' or 'remove'.",
                code='invalid_action',
            )
        return Response(SuccessAPIResponse(
            message='User preferred categories updated successfully.'
        ).to_dict(), status=status.HTTP_200_OK)
