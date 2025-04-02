from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        """
        Logs out the user by deleting the session cookie.
        """
        response = Response({'success': 'User logged out successfully.'})
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response