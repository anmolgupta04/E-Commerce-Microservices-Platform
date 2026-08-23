import logging

from .models import Notification

logger = logging.getLogger("notifications")

TEMPLATES = {
    "order.created": "Hi {username}, we received your order #{order_id} for {total_amount}. We'll email you once payment clears.",
    "order.paid": "Hi {username}, payment for order #{order_id} succeeded ({amount}). It's on its way!",
    "order.payment_failed": "Hi {username}, payment for order #{order_id} failed: {reason}. Please try again.",
}


def handle_event(event_type: str, data: dict) -> Notification:
    message = TEMPLATES[event_type].format(**data)
    notification = Notification.objects.create(
        order_id=data["order_id"],
        recipient=data.get("username", "unknown"),
        event_type=event_type,
        message=message,
    )
    logger.info("MOCK SEND -> %s: %s", notification.recipient, notification.message)
    return notification
