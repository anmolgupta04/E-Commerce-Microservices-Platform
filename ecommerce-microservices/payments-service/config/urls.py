from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/payments/", include("payments.urls")),
    path("health/", lambda r: JsonResponse({"service": "payments", "status": "ok"})),
]
