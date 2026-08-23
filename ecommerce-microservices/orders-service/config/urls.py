from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/orders/", include("orders.urls")),
    path("health/", lambda r: JsonResponse({"service": "orders", "status": "ok"})),
]
