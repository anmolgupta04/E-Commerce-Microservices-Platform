from django.urls import path
from .views import PaymentListView, OrderCreatedWebhook

urlpatterns = [
    path("", PaymentListView.as_view(), name="payment-list"),
    path("events/order-created/", OrderCreatedWebhook.as_view(), name="event-order-created"),
]
