from django.conf import settings
from rest_framework.permissions import BasePermission


class IsInternalService(BasePermission):
    message = "missing or invalid internal service token"

    def has_permission(self, request, view):
        token = request.headers.get("X-Internal-Token", "")
        return token == settings.INTERNAL_SERVICE_TOKEN
