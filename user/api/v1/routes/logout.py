from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.api_responses import SuccessAPIResponse
from user.api.v1.swagger import logout_schema
from user.domain.exceptions import AuthenticationServiceError
from user.services.authentication import SESSION_ID_CLAIM, revoke_session


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    @extend_schema(**logout_schema)
    def post(self, request):
        # The authenticated access token identifies this login session.
        session_id = request.auth.get(SESSION_ID_CLAIM)

        if session_id:
            try:
                revoke_session(
                    session_id=session_id,
                    user=request.user,
                )
            except AuthenticationServiceError:
                # Still clear the browser's authentication cookies.
                # An invalid session identifier must not prevent logout.
                pass

        response = Response(
            SuccessAPIResponse(
                message="Log out successful."
            ).to_dict(),
            status=200,
        )

        cookie_config = settings.SIMPLE_JWT

        response.delete_cookie(
            key="access_token",
            path=cookie_config["AUTH_COOKIE_PATH"],
            samesite=cookie_config["AUTH_COOKIE_SAMESITE"],
        )

        response.delete_cookie(
            key="refresh_token",
            path=cookie_config["AUTH_COOKIE_PATH"],
            samesite=cookie_config["AUTH_COOKIE_SAMESITE"],
        )

        return response
