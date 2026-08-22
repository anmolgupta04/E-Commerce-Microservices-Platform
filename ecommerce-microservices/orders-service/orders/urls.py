from django.urls import path
from .views import OrderListCreateView, OrderDetailView, MarkOrderPaidView, MarkOrderPaymentFailedView

urlpatterns = [
    path("", OrderListCreateView.as_view(), name="order-list-create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/mark-paid/", MarkOrderPaidView.as_view(), name="order-mark-paid"),
    path("<int:pk>/mark-payment-failed/", MarkOrderPaymentFailedView.as_view(), name="order-mark-payment-failed"),
]
