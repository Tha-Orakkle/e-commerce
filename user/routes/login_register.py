from datetime import timedelta
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from user.models import User
from user.serializers import UserSerializer
from user.tasks import send_verification_mail_task

class RegisterView(APIView):

    def post(self, request):
        """
        Handle the user registration process.
        Expects 'email' and 'password' in the request data.
        """
        data = request.data
        if not data or not data.get('email') or not data.get('password'):
            return Response({'error': 'Please provide email and password.'}, status=400)
        if data.get('password') != data.get('confirm_password', None):
            return Response({'error': 'Passwords do not match.'})
        try:
            user = User.objects.create_user(
                email=data.get('email'), password=data.get('password'))
        except (ValidationError, ValueError) as e:
            return Response({'error': str(e)}, status=400)
        send_verification_mail_task.delay(str(user.id), user.email)
        return Response({'success': f'User {user.email} created successfully'}, status=201)
    

class LoginView(APIView):

    def post(self, request):
        """
        Takes user email and password for authentication. 
        Returns access_token and refresh_token cookies.
        """
        email = request.data.get('email', None)
        pwd = request.data.get('password', None)
        remember_me = request.data.get('remember_me', False)
        lifespan = timedelta(days=7) if remember_me else timedelta(days=1)

        if not email or not pwd:
            return Response({'error': 'Please provide email and password.'}, status=400)
        user = authenticate(email=email, password=pwd)
        if not user:
            return Response({'error': 'Invalid login credentials.'}, status=400)
        refresh = RefreshToken.for_user(user)
        refresh.set_exp(lifetime=lifespan)
        response = Response({'success': f'User {user.email} login succesful.'})
        response.set_cookie(
            'refresh_token', str(refresh),
            httponly=True, secure=False,
            samesite='Lax', max_age=(604800 if remember_me else 86400)
        )
        response.set_cookie(
            'access_token', str(refresh.access_token),
            httponly=True, secure=False,
            samesite='Lax', max_age=3600 # 1 hr
        )
        return response


class UserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id=None):
        """
        Gets a specific user where id is not None.
        Otherwise returns all users
        """
        if not id:
            users = User.objects.all()
            serializers = UserSerializer(users, many=True)
            return Response(serializers.data)
        user = User.objects.filter(id=id).first()
        if not user:
            return Response({'error': 'Invalid user id.'}, status=400)
        serializer = UserSerializer(user)
        return Response(serializer.data)
