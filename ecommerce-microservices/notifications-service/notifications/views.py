from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer
from .handlers import handle_event
from .permissions import IsInternalService


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all().order_by("-created_at")


class BaseEventWebhook(APIView):
    permission_classes = [IsInternalService]
    event_type = None

    def post(self, request):
        notification = handle_event(self.event_type, request.data)
        return Response(NotificationSerializer(notification).data, status=201)


class OrderCreatedWebhook(BaseEventWebhook):
    event_type = "order.created"


class OrderPaidWebhook(BaseEventWebhook):
    event_type = "order.paid"


class OrderPaymentFailedWebhook(BaseEventWebhook):
    event_type = "order.payment_failed"
