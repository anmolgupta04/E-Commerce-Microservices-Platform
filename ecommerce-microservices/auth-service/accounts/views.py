from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.models import User

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyTokenView(APIView):
    """
    Internal service-to-service endpoint. Orders/Catalog/Payments call this
    (synchronous REST call) instead of decoding JWTs themselves, so the Auth
    service stays the single source of truth for identity.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token", "")
        try:
            access = AccessToken(token)
            user = User.objects.get(id=access["user_id"])
        except (TokenError, User.DoesNotExist, KeyError):
            return Response({"valid": False}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(
            {
                "valid": True,
                "user_id": user.id,
                "username": user.username,
                "is_staff": user.is_staff,
            }
        )
