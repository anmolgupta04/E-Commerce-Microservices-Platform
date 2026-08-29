from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.conf import settings

from .models import Product


class ProductStockTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(name="Widget", price="9.99", stock=5, sku="SKU-1")

    def test_public_can_list_products(self):
        resp = self.client.get("/api/catalog/products/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_adjust_stock_requires_internal_token(self):
        resp = self.client.post(f"/api/catalog/products/{self.product.id}/adjust-stock/", {"quantity": -1})
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_adjust_stock_rejects_overdraw(self):
        resp = self.client.post(
            f"/api/catalog/products/{self.product.id}/adjust-stock/",
            {"quantity": -999},
            HTTP_X_INTERNAL_TOKEN=settings.INTERNAL_SERVICE_TOKEN,
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
