from django.urls import path
from .views import NotificationListView, OrderCreatedWebhook, OrderPaidWebhook, OrderPaymentFailedWebhook

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("events/order-created/", OrderCreatedWebhook.as_view(), name="event-order-created"),
    path("events/order-paid/", OrderPaidWebhook.as_view(), name="event-order-paid"),
    path("events/order-payment-failed/", OrderPaymentFailedWebhook.as_view(), name="event-order-payment-failed"),
]
