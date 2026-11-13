"""Contract/security tests for the additive /api/v1/ boundary.

Run with: python manage.py test tests.test_api_v1 --settings=mouod.test_settings
No production database is used by the test settings.
"""
import json

from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.missions.models import Mission
from apps.treasure.models import TreasureCategory, TreasureItem
from apps.wallet.models import PointTransaction


class ApiV1AuthTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username="apiuser", email="apiuser@example.com", password="Valid-Password-179!",
        )

    def _csrf(self):
        self.assertEqual(self.client.get(reverse("api_v1:csrf")).status_code, 200)
        return self.client.cookies["csrftoken"].value

    def test_login_requires_csrf_and_returns_only_allowlisted_fields(self):
        url = reverse("api_v1:login")
        body = json.dumps({"username": "apiuser", "password": "Valid-Password-179!"})
        response = self.client.post(url, body, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        token = self._csrf()
        response = self.client.post(url, body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        user = response.json()["user"]
        self.assertEqual(user["username"], "apiuser")
        self.assertNotIn("password", user)
        self.assertNotIn("is_staff", user)
        self.assertNotIn("is_superuser", user)

    def test_logout_requires_csrf(self):
        token = self._csrf()
        self.client.force_login(self.user)
        response = self.client.post(reverse("api_v1:logout"))
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse("api_v1:logout"), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_registration_cannot_set_staff_or_balances(self):
        token = self._csrf()
        body = json.dumps({
            "username": "new_member", "email": "new_member@example.com",
            "password": "S3cure-Pass-W0rd!", "is_staff": True,
            "total_coins": 999999,
        })
        response = self.client.post(reverse("api_v1:register"), body,
                                    content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        new_user = User.objects.get(username="new_member")
        self.assertFalse(new_user.is_staff)
        self.assertEqual(new_user.total_coins, 0)


class ApiV1ReadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="owner", password="Password-179!!", total_coins=30)
        self.other = User.objects.create_user(username="other", password="Password-179!!")

    def test_anonymous_profile_forbidden(self):
        response = self.client.get(reverse("api_v1:me"))
        self.assertIn(response.status_code, (401, 403))

    def test_wallet_transactions_are_owner_only(self):
        PointTransaction.objects.create(
            user=self.user, transaction_type="mission", title="mine", points=10, coins=1,
        )
        PointTransaction.objects.create(
            user=self.other, transaction_type="bonus", title="SECRET OTHER", points=999,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("api_v1:transactions"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["title"], "mine")
        wallet = self.client.get(reverse("api_v1:wallet"))
        self.assertEqual(wallet.json()["total_coins"], 30)

    def test_missions_only_show_eligible_global_for_user_without_team(self):
        Mission.objects.create(title="visible", is_global=True, is_active=True)
        Mission.objects.create(title="hidden team mission", is_global=False, is_active=True)
        self.client.force_login(self.user)
        response = self.client.get(reverse("api_v1:missions"))
        self.assertEqual(response.status_code, 200)
        titles = [mission["title"] for mission in response.json()["results"]]
        self.assertIn("visible", titles)
        self.assertNotIn("hidden team mission", titles)

    def test_catalog_returns_only_active_items_and_is_read_only(self):
        category = TreasureCategory.objects.create(name="Gifts", slug="gifts")
        TreasureItem.objects.create(name="active", image="treasure/items/test.jpg", category=category,
                                    is_active=True, price=10)
        TreasureItem.objects.create(name="hidden", image="treasure/items/test.jpg", category=category,
                                    is_active=False, price=10)
        self.client.force_login(self.user)
        url = reverse("api_v1:treasure_items")
        response = self.client.get(url, {"category": "gifts"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.json()["results"]], ["active"])
        self.assertEqual(self.client.post(url, data={}, content_type="application/json").status_code, 405)
