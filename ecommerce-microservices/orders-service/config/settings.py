import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-orders-service-change-in-prod")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "orders.authentication.StatelessJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "SIGNING_KEY": os.environ.get("JWT_SIGNING_KEY", "shared-jwt-signing-key-for-all-services-dev"),
    "ALGORITHM": "HS256",
}

# --- Service discovery (env-driven so K8s can override with Service DNS names) ---
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8001")
CATALOG_SERVICE_URL = os.environ.get("CATALOG_SERVICE_URL", "http://localhost:8002")

# --- Event bus ---
# "amqp"  -> publish to RabbitMQ (production / docker-compose / k8s)
# "http"  -> direct HTTP fan-out to subscriber webhooks (zero-infra local demo)
EVENT_BUS_MODE = os.environ.get("EVENT_BUS_MODE", "http")
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
EVENT_SUBSCRIBERS = {
    "order.created": [
        os.environ.get("PAYMENTS_SERVICE_URL", "http://localhost:8004") + "/api/payments/events/order-created/",
        os.environ.get("NOTIFICATIONS_SERVICE_URL", "http://localhost:8005") + "/api/notifications/events/order-created/",
    ],
    "order.paid": [
        os.environ.get("NOTIFICATIONS_SERVICE_URL", "http://localhost:8005") + "/api/notifications/events/order-paid/",
    ],
    "order.payment_failed": [
        os.environ.get("NOTIFICATIONS_SERVICE_URL", "http://localhost:8005") + "/api/notifications/events/order-payment-failed/",
    ],
}

INTERNAL_SERVICE_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "dev-internal-service-token-change-in-prod")
