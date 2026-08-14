from django.test import TestCase
from decimal import Decimal
from .gateway import charge


class GatewayTests(TestCase):
    def test_normal_amount_succeeds(self):
        result = charge(order_id=1, amount=Decimal("42.00"))
        self.assertTrue(result["success"])

    def test_multiple_of_666_declines(self):
        result = charge(order_id=2, amount=Decimal("1332.00"))
        self.assertFalse(result["success"])
