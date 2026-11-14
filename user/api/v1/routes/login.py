from datetime import timedelta

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.authentication.cookies import set_auth_cookie
from common.exceptions import ErrorException
from common.utils.api_responses import SuccessAPIResponse
from common.utils.bools import parse_bool
from user.api.v1.serializers import UserSerializer
from user.api.v1.swagger import customer_login_schema, staff_login_schema
from user.services.authentication import create_session_tokens


class ShopOwnerOrStaffLoginView(APIView):
    authentication_classes = []  # noqa: RUF012
    permission_classes = [AllowAny]  # noqa: RUF012

    @extend_schema(**staff_login_schema)
    def post(self, request):
        """
        Log staff and shop owner in.
        Take the shop_code, staff_handle and the password.
        """
        errors = {}
        shop_code = request.data.get("shop_code", "").strip().upper()
        staff_handle = request.data.get("staff_handle", "").strip()
        pwd = request.data.get("password", "").strip()
        remember_me = parse_bool(request.data.get("remember_me", False))
        lifespan = timedelta(days=30) if remember_me else timedelta(days=1)

        if not shop_code:
            errors["shop_code"] = ["This field is required."]
        if not staff_handle:
            errors["staff_handle"] = ["This field is required."]
        if not pwd:
            errors["password"] = ["This field is required."]

        if errors:
            raise ErrorException(
                detail="Log in failed.",
                code="validation_error",
                errors=errors
            )
        user = authenticate(
            shop_code=shop_code,
            staff_handle=staff_handle,
            password=pwd
        )

        if not user or (user and not user.is_staff):
            raise ErrorException(
                detail="Log in failed.",
                code="invalid_credentials",
                errors={"non_field_errors": [
                    "Invalid login credentials were provided."
                ]}
            )
        serializer = UserSerializer(user)
        response = Response(
            SuccessAPIResponse(
                message="Log in successful.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
        tokens = create_session_tokens(user=user, lifetime=lifespan)

        set_auth_cookie(
            response,
            "refresh_token",
            tokens["refresh"],
            max_age=lifespan.total_seconds()
        )
        set_auth_cookie(
            response,
            "access_token",
            tokens["access"]
        )

        return response


class CustomerLoginView(APIView):
    authentication_classes = []  # noqa: RUF012
    permission_classes = [AllowAny]  # noqa: RUF012

    @extend_schema(**customer_login_schema)
    def post(self, request):
        """
        Takes user email and password for authentication.
        Returns access_token and refresh_token cookies.
        """
        errors = {}
        email = request.data.get("email", None)
        pwd = request.data.get("password", None)
        remember_me = parse_bool(request.data.get("remember_me", False))
        lifespan = timedelta(days=30) if remember_me else timedelta(days=1)

        if not email:
            errors["email"] = ["This field is required."]
        if not pwd:
            errors["password"] = ["This field is required."]

        if errors:
            raise ErrorException(
                detail="Log in failed.",
                code="validation_error",
                errors=errors
            )

        user = authenticate(email=email, password=pwd)
        if not user or (user and not user.is_customer):
            raise ErrorException(
                detail="Log in failed.",
                code="invalid_credentials",
                errors={"non_field_errors": [
                    "Invalid login credentials were provided."]}
            )

        serializer = UserSerializer(user)
        response = Response(
            SuccessAPIResponse(
                message="Log in successful.",
                data=serializer.data,
            ).to_dict(), status=status.HTTP_200_OK)

        tokens = create_session_tokens(user=user, lifetime=lifespan)

        set_auth_cookie(
            response,
            "refresh_token",
            tokens["refresh"],
            max_age=lifespan.total_seconds()
        )
        set_auth_cookie(
            response,
            "access_token",
            tokens["access"]
        )

        return response
