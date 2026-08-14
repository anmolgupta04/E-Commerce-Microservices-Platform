from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import PaymentSerializer
from .handlers import handle_order_created
from .permissions import IsInternalService


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all().order_by("-created_at")


class OrderCreatedWebhook(APIView):
    """
    HTTP transport for the "order.created" event (used when EVENT_BUS_MODE=http).
    In the docker-compose/K8s deployment with EVENT_BUS_MODE=amqp, the same
    handle_order_created() logic instead runs inside consume_events, driven
    by a RabbitMQ queue -- Orders never calls this URL in that mode.
    """

    permission_classes = [IsInternalService]

    def post(self, request):
        payment = handle_order_created(request.data)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
