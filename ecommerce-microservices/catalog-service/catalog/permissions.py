from django.conf import settings
from rest_framework.permissions import BasePermission


class IsInternalService(BasePermission):
    """
    Gate for service-to-service webhooks/endpoints (stock adjustment, event
    webhooks). Callers must present the shared internal token in the
    X-Internal-Token header -- a stand-in here for mTLS / a service mesh
    identity in the real K8s deployment (see k8s/*-networkpolicy.yaml).
    """

    message = "missing or invalid internal service token"

    def has_permission(self, request, view):
        token = request.headers.get("X-Internal-Token", "")
        return token == settings.INTERNAL_SERVICE_TOKEN
