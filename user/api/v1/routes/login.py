from datetime import timedelta
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny 
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from common.utils.api_responses import SuccessAPIResponse
from common.utils.bools import parse_bool
from common.exceptions import ErrorException
from user.api.v1.swagger import (
    admin_login_schema,
    customer_login_schema
)   
from user.api.v1.serializers import UserSerializer


class ShopOwnerOrStaffLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(**admin_login_schema)
    def post(self, request):
        """
        Sign the admin user (staff and shop owner) in.
        Take the shop_code, staff_id and the password.
        """
        errors = {}
        shop_code = request.data.get('shop_code', '').strip().upper()
        staff_handle = request.data.get('staff_id', '').strip()
        pwd = request.data.get('password', '').strip()
        remember_me = parse_bool(request.data.get('remember_me', False))
        lifespan = timedelta(days=7) if remember_me else timedelta(days=1)

        if not shop_code:
            errors['shop_code'] = ['This field is required.']
        if not staff_handle:
            errors['staff_handle'] = ['This field is required.']
        if not pwd:
            errors['password'] = ['This field is required.']
        
        if errors:
            raise ErrorException(
                detail="Admin login failed.",
                code="validation_error",
                errors=errors
            )
        admin_user = authenticate(shop_code=shop_code, staff_handle=staff_handle, password=pwd)
        if not admin_user or (admin_user and not admin_user.is_staff):
            raise ErrorException(
                detail="Admin login failed.",
                code="invalid_credentials",
                errors={'non_field_errors': ['Invalid login credentials were provided.']}
            )
        serializer = UserSerializer(admin_user)
        response = Response(
            SuccessAPIResponse(
                message="Admin login successful.",
                data=serializer.data
            ).to_dict(), status=status.HTTP_200_OK
        )
        refresh = RefreshToken.for_user(admin_user)
        refresh.set_exp(lifetime=lifespan)
        response.set_cookie(
            'refresh_token', str(refresh),
            httponly=True, secure=False,
            samesite='Lax', max_age=(604800 if remember_me else 86400)
        )
        response.set_cookie(
            'access_token', str(refresh.access_token),
            httponly=True, secure=False,
            samesite='Lax'
        )
        return response
    

class CustomerLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(**customer_login_schema)
    def post(self, request):
        """
        Takes user email and password for authentication. 
        Returns access_token and refresh_token cookies.
        """
        errors = {}
        email = request.data.get('email', None)
        pwd = request.data.get('password', None)
        remember_me = request.data.get('remember_me', False)
        lifespan = timedelta(days=7) if remember_me else timedelta(days=1)
        
        if not email:
            errors['email'] = ['This field is required.']
        if not pwd:
            errors['password'] = ['This field is required.']
        
        if errors:
            raise ErrorException(
                detail="Customer login failed.",
                code="validation_error",
                errors=errors
            )    
            
        user = authenticate(email=email, password=pwd)
        if not user or (user and not user.is_customer):
            raise ErrorException(
                detail="Customer login failed.",
                code="invalid_credentials",
                errors={'non_field_errors': ['Invalid login credentials were provided.']}
            )

        serializer = UserSerializer(user)
        response = Response(
            SuccessAPIResponse(
                message=f'Customer login successful.',
                data=serializer.data,
            ).to_dict(), status=status.HTTP_200_OK)
        refresh = RefreshToken.for_user(user)
        refresh.set_exp(lifetime=lifespan)
        response.set_cookie(
            'refresh_token', str(refresh),
            httponly=True, secure=False,
            samesite='Lax', max_age=(604800 if remember_me else 86400)
        )
        response.set_cookie(
            'access_token', str(refresh.access_token),
            httponly=True, secure=False,
            samesite='Lax'
        )
        return response
