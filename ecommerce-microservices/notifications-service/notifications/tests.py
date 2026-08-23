from django.test import TestCase
from .handlers import handle_event
from .models import Notification


class NotificationHandlerTests(TestCase):
    def test_order_created_renders_template_and_saves(self):
        n = handle_event("order.created", {
            "order_id": 7, "username": "bob", "total_amount": "19.99"
        })
        self.assertIn("bob", n.message)
        self.assertIn("#7", n.message)
        self.assertEqual(Notification.objects.count(), 1)
