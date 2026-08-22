from decimal import Decimal

from django.db import transaction
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from .services import verify_token, get_product, adjust_stock, UpstreamServiceError
from .eventbus import publish_event
from .permissions import IsInternalService


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.all().order_by("-created_at")
        if not getattr(user, "is_staff", False):
            qs = qs.filter(user_id=user.id)
        return qs

    def create(self, request, *args, **kwargs):
        input_serializer = OrderCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        items_input = input_serializer.validated_data["items"]

        # 1. Sync call -> Auth service: confirm this JWT is genuinely valid,
        #    not just locally decodable (defense in depth beyond the shared
        #    signing key check DRF already did to reach this view).
        raw_token = request.META.get("HTTP_AUTHORIZATION", "").replace("Bearer ", "")
        auth_info = verify_token(raw_token)

        # 2. Sync calls -> Catalog service: price each line item, then
        #    reserve stock. If any reservation fails, roll back the ones
        #    that already succeeded so we never leave stock over-reserved.
        reserved = []
        order_items_data = []
        total = Decimal("0.00")
        try:
            for item in items_input:
                product = get_product(item["product_id"])
                adjust_stock(item["product_id"], -item["quantity"])
                reserved.append((item["product_id"], item["quantity"]))
                unit_price = Decimal(str(product["price"]))
                total += unit_price * item["quantity"]
                order_items_data.append(
                    {
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "unit_price": unit_price,
                        "quantity": item["quantity"],
                    }
                )
        except UpstreamServiceError as exc:
            for product_id, quantity in reserved:
                try:
                    adjust_stock(product_id, quantity)  # roll back
                except UpstreamServiceError:
                    pass  # best-effort compensation; would go to a dead-letter queue in prod
            return Response({"detail": str(exc)}, status=exc.status_code)

        # 3. Local transaction: the order only exists once every upstream
        #    call above has already succeeded.
        with transaction.atomic():
            order = Order.objects.create(
                user_id=auth_info["user_id"],
                username=auth_info["username"],
                status="pending_payment",
                total_amount=total,
            )
            OrderItem.objects.bulk_create(
                [OrderItem(order=order, **data) for data in order_items_data]
            )

        # 4. Async: publish order.created. Payments and Notifications each
        #    consume this independently -- Orders doesn't wait for either.
        publish_event(
            "order.created",
            {
                "order_id": order.id,
                "user_id": order.user_id,
                "username": order.username,
                "total_amount": str(order.total_amount),
                "items": [
                    {"product_id": d["product_id"], "product_name": d["product_name"], "quantity": d["quantity"]}
                    for d in order_items_data
                ],
            },
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()


class MarkOrderPaidView(APIView):
    """Called by the Payments service once a (mocked) charge succeeds."""

    permission_classes = [IsInternalService]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "order not found"}, status=404)
        order.status = "paid"
        order.save(update_fields=["status", "updated_at"])
        return Response(OrderSerializer(order).data)


class MarkOrderPaymentFailedView(APIView):
    """
    Called by the Payments service if a (mocked) charge fails. Rolls the
    reserved stock back via Catalog so failed orders don't hold inventory.
    """

    permission_classes = [IsInternalService]

    def post(self, request, pk):
        try:
            order = Order.objects.select_related().prefetch_related("items").get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "order not found"}, status=404)

        for item in order.items.all():
            try:
                adjust_stock(item.product_id, item.quantity)
            except UpstreamServiceError:
                pass

        order.status = "payment_failed"
        order.save(update_fields=["status", "updated_at"])
        return Response(OrderSerializer(order).data)
