from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.api_responses import SuccessAPIResponse
from common.exceptions import ErrorException
from common.permissions import IsCustomerOrShopOwner
from user.api.v1.serializers import UserUpdateSerializer, UserSerializer
from user.tasks import send_verification_mail_task

class UpdateUserView(APIView):
    permission_classes = [IsCustomerOrShopOwner]
    
    def patch(self, request):
        """
        Update a user's (customer or shopowner) email or staff handle
        """
        serializer = UserUpdateSerializer(
            data=request.data,
            context = {'request': request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
        except ValidationError as e:
            raise ErrorException(
                detail='User update failed.',
                code='validation_error',
                errors=e.detail 
            )

        # if email was updated, send a verification mail
        if not user.is_verified:
            send_verification_mail_task.delay(str(user.id), user.email)
            
        return Response(SuccessAPIResponse(
            message="User updated successfully.",
            data=UserSerializer(user).data
        ).to_dict(), status=status.HTTP_200_OK)
