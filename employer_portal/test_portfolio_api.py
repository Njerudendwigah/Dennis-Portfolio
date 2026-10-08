import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from .portfolio_models import PortfolioContent


@override_settings(
    PORTFOLIO_ADMIN_ORIGIN="https://njerudendwigah.github.io",
    PORTFOLIO_API_TOKEN_MAX_AGE=28800,
)
class PortfolioApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="dennis",
            email="dennis@example.com",
            password="StrongPass123!",
            is_staff=True,
            is_active=True,
        )
        self.origin = "https://njerudendwigah.github.io"

    def login(self):
        response = self.client.post(
            "/employer/api/portfolio/login/",
            data=json.dumps(
                {
                    "email": "dennis@example.com",
                    "password": "StrongPass123!",
                }
            ),
            content_type="application/json",
            HTTP_ORIGIN=self.origin,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        self.assertIn("Access-Control-Allow-Origin", response)
        return response.json()["token"]

    def test_login_rejects_non_staff_user(self):
        self.user.is_staff = False
        self.user.save(update_fields=["is_staff"])

        response = self.client.post(
            "/employer/api/portfolio/login/",
            data=json.dumps(
                {
                    "email": "dennis@example.com",
                    "password": "StrongPass123!",
                }
            ),
            content_type="application/json",
            HTTP_ORIGIN=self.origin,
        )

        self.assertEqual(response.status_code, 401)

    def test_login_returns_signed_token_for_staff_user(self):
        token = self.login()
        self.assertTrue(token)

    def test_data_requires_bearer_token(self):
        response = self.client.get(
            "/employer/api/portfolio/data/",
            HTTP_ORIGIN=self.origin,
        )

        self.assertEqual(response.status_code, 401)

    def test_staff_can_read_and_write_portfolio_sections(self):
        token = self.login()
        headers = {
            "HTTP_AUTHORIZATION": f"Bearer {token}",
            "HTTP_ORIGIN": self.origin,
        }

        payload = {
            "fullName": "Dennis Ndwigah Njeru",
            "headline": "Supply Chain & Operations Professional",
        }

        response = self.client.put(
            "/employer/api/portfolio/data/portfolioProfile/",
            data=json.dumps(payload),
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            PortfolioContent.objects.get(key="portfolioProfile").data,
            payload,
        )

        response = self.client.get(
            "/employer/api/portfolio/data/",
            **headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["sections"]["portfolioProfile"],
            payload,
        )

    def test_unknown_section_is_rejected(self):
        token = self.login()

        response = self.client.put(
            "/employer/api/portfolio/data/not-allowed/",
            data=json.dumps({"value": True}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_ORIGIN=self.origin,
        )

        self.assertEqual(response.status_code, 404)
