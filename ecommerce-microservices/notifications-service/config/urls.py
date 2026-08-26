from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/notifications/", include("notifications.urls")),
    path("health/", lambda r: JsonResponse({"service": "notifications", "status": "ok"})),
]
