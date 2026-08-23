from django.db import models


class Notification(models.Model):
    order_id = models.PositiveIntegerField()
    recipient = models.CharField(max_length=150)
    event_type = models.CharField(max_length=40)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.event_type}] to {self.recipient} (order #{self.order_id})"
