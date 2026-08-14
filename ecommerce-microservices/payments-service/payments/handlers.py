"""
Event handling logic shared by both transports:
  - OrderCreatedWebhook (HTTP, used in EVENT_BUS_MODE=http / this sandbox demo)
  - consume_events management command (AMQP, used with docker-compose/K8s + RabbitMQ)

Keeping the actual business logic here means the transport is just plumbing.
"""
from decimal import Decimal

import requests
from django.conf import settings

from .models import Payment
from .gateway import charge
from .eventbus import publish_event


def handle_order_created(data: dict) -> Payment:
    order_id = data["order_id"]
    amount = Decimal(str(data["total_amount"]))

    result = charge(order_id, amount)

    if result["success"]:
        payment = Payment.objects.create(
            order_id=order_id,
            user_id=data["user_id"],
            amount=amount,
            status="succeeded",
            gateway_reference=result["reference"],
        )
        _callback_orders(order_id, "mark-paid")
        publish_event("order.paid", {"order_id": order_id, "username": data.get("username"), "amount": str(amount)})
    else:
        payment = Payment.objects.create(
            order_id=order_id,
            user_id=data["user_id"],
            amount=amount,
            status="failed",
            failure_reason=result["reason"],
        )
        _callback_orders(order_id, "mark-payment-failed")
        publish_event(
            "order.payment_failed",
            {"order_id": order_id, "username": data.get("username"), "reason": result["reason"]},
        )
    return payment


def _callback_orders(order_id, action):
    try:
        requests.post(
            f"{settings.ORDERS_SERVICE_URL}/api/orders/{order_id}/{action}/",
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_TOKEN},
            timeout=5,
        )
    except requests.RequestException:
        pass
