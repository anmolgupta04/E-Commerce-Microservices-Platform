from decimal import Decimal
from django.test import TestCase
from .models import Order, OrderItem


class OrderModelTests(TestCase):
    def test_order_total_matches_item_subtotals(self):
        order = Order.objects.create(user_id=1, username="carol", status="pending_payment", total_amount=Decimal("39.98"))
        OrderItem.objects.create(order=order, product_id=1, product_name="Widget", unit_price=Decimal("19.99"), quantity=2)
        self.assertEqual(order.items.first().subtotal, Decimal("39.98"))
