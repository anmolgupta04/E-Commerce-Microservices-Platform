from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending_payment", "Pending Payment"),
        ("paid", "Paid"),
        ("payment_failed", "Payment Failed"),
        ("cancelled", "Cancelled"),
    ]

    user_id = models.PositiveIntegerField()
    username = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_payment")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_id = models.PositiveIntegerField()
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
