from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "order_id", "user_id", "amount", "status", "gateway_reference", "failure_reason", "created_at")
