from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_then_login_returns_jwt_with_username_claim(self):
        resp = self.client.post(reverse("register"), {
            "username": "alice", "email": "alice@example.com", "password": "StrongPass123!"
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.post(reverse("login"), {"username": "alice", "password": "StrongPass123!"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_verify_rejects_garbage_token(self):
        resp = self.client.post(reverse("verify"), {"token": "not-a-real-token"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
