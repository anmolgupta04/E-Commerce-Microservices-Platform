"""
Stateless JWT authentication for downstream services.

The Auth service is the only place with a real User table. Every other
service trusts JWTs signed with the shared SIMPLE_JWT signing key and
builds a lightweight, non-persisted "RemoteUser" straight from the token
claims -- no local DB lookup, no local User table to keep in sync.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication


class RemoteUser:
    """Minimal stand-in for django.contrib.auth.models.User."""

    def __init__(self, user_id, username):
        self.id = user_id
        self.pk = user_id
        self.username = username
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return self.username


class StatelessJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        username = validated_token.get("username", f"user-{user_id}")
        if user_id is None:
            return None
        return RemoteUser(user_id, username)
