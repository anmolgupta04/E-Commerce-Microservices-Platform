"""
Synchronous inter-service calls made while placing an order:
  Orders -> Auth    : verify the caller's JWT is real (not just locally decoded)
  Orders -> Catalog : fetch live price + atomically reserve stock

Kept in one module so the view stays about HTTP request/response shape,
not about which other services it has to talk to.
"""
import requests
from django.conf import settings


class UpstreamServiceError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def verify_token(raw_token: str) -> dict:
    try:
        resp = requests.post(
            f"{settings.AUTH_SERVICE_URL}/api/auth/verify/",
            json={"token": raw_token},
            timeout=5,
        )
    except requests.RequestException as exc:
        raise UpstreamServiceError(f"auth service unreachable: {exc}", 503)

    if resp.status_code != 200:
        raise UpstreamServiceError("token could not be verified by auth service", 401)
    return resp.json()


def get_product(product_id: int) -> dict:
    try:
        resp = requests.get(
            f"{settings.CATALOG_SERVICE_URL}/api/catalog/products/{product_id}/",
            timeout=5,
        )
    except requests.RequestException as exc:
        raise UpstreamServiceError(f"catalog service unreachable: {exc}", 503)

    if resp.status_code == 404:
        raise UpstreamServiceError(f"product {product_id} does not exist", 400)
    if resp.status_code != 200:
        raise UpstreamServiceError("catalog service error", 502)
    return resp.json()


def adjust_stock(product_id: int, quantity_delta: int) -> dict:
    """quantity_delta is negative to reserve stock, positive to roll back."""
    try:
        resp = requests.post(
            f"{settings.CATALOG_SERVICE_URL}/api/catalog/products/{product_id}/adjust-stock/",
            json={"quantity": quantity_delta},
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_TOKEN},
            timeout=5,
        )
    except requests.RequestException as exc:
        raise UpstreamServiceError(f"catalog service unreachable: {exc}", 503)

    if resp.status_code == 409:
        raise UpstreamServiceError(f"insufficient stock for product {product_id}", 409)
    if resp.status_code != 200:
        raise UpstreamServiceError("catalog service error while adjusting stock", 502)
    return resp.json()
