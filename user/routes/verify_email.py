from rest_framework.views import APIView
from rest_framework.response import Response
from user.utils.email_verification import verify_email_verification_token


class VerifyEmailView(APIView):
    def get(self, request):
        """
        Verifies the token from the request.
        """
        token = request.GET.get('token', None)
        if not token:
            return Response({'error': 'Token not provided.'}, status=400)
        user = verify_email_verification_token(token)
        if not user:
            return Response({'error': 'Invalid or expired token.'}, status=400)
        user.is_verified = True
        user.save()
        return Response({'success': 'Email verified successfully.'})