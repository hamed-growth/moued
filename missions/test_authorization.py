from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse

from .models import User


class AuthorizationTests(TestCase):
    def setUp(self):
        self.target = User.objects.create_user(username="target")
        self.staff = User.objects.create_user(username="staff", is_staff=True)
        self.root = User.objects.create_superuser(username="root")
        self.manager = User.objects.create_user(username="manager", is_team_manager=True)
        self.permission = Permission.objects.get(
            content_type__app_label="missions", codename="change_user",
        )
        self.staff.user_permissions.add(self.permission)
        self.group = Group.objects.create(name="fixture group")
        self.toggle_url = reverse("dashboard:user_toggle_staff", args=[self.target.pk])

    def test_anonymous_and_team_manager_cannot_toggle_staff(self):
        response = self.client.post(self.toggle_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("next=", response.url)
        self.client.force_login(self.manager)
        response = self.client.post(self.toggle_url)
        self.assertRedirects(response, reverse("missions:home"), fetch_redirect_response=False)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_staff)

    def test_staff_cannot_revoke_or_toggle_own_privilege(self):
        self.client.force_login(self.staff)
        self.target.is_staff = True
        self.target.save(update_fields=["is_staff"])
        for user in (self.target, self.staff):
            with self.subTest(user=user.username):
                url = reverse("dashboard:user_toggle_staff", args=[user.pk])
                self.assertEqual(self.client.post(url).status_code, 403)
                user.refresh_from_db()
                self.assertTrue(user.is_staff)

    def test_superuser_can_grant_and_revoke_but_not_toggle_self(self):
        self.client.force_login(self.root)
        self.assertEqual(self.client.get(self.toggle_url).status_code, 405)
        for expected in (True, False):
            self.assertEqual(self.client.post(self.toggle_url, {"is_superuser": "on"}).status_code, 302)
            self.target.refresh_from_db()
            self.assertEqual(self.target.is_staff, expected)
            self.assertFalse(self.target.is_superuser)
        url = reverse("dashboard:user_toggle_staff", args=[self.root.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.root.refresh_from_db()
        self.assertTrue(self.root.is_staff)

    def test_superuser_toggle_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.root)
        self.assertEqual(client.post(self.toggle_url).status_code, 403)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_staff)
        detail = reverse("dashboard:user_detail", args=[self.target.pk])
        self.assertEqual(client.get(detail).status_code, 200)
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post(self.toggle_url, {"csrfmiddlewaretoken": token}).status_code, 302)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_staff)

    def test_staff_retains_team_manager_and_active_operations(self):
        self.client.force_login(self.staff)
        for route in ("dashboard:user_toggle_manager", "dashboard:user_toggle_active"):
            self.assertEqual(self.client.post(reverse(route, args=[self.target.pk])).status_code, 302)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_team_manager)
        self.assertFalse(self.target.is_active)
        self.assertFalse(self.target.is_staff)

    def user_form(self, user, **fields):
        return {
            "username": user.username, "password": user.password,
            "first_name": "Updated", "is_active": "on",
            "total_points": 0, "total_coins": 0, "activity_streak": 0,
            "date_joined_0": "2026-01-01", "date_joined_1": "12:00:00",
            **fields,
        }

    def test_user_admin_rejects_each_privilege_field_without_partial_edit(self):
        self.client.force_login(self.staff)
        url = reverse("admin:missions_user_change", args=[self.target.pk])
        for field, value in {
            "is_staff": "on", "is_superuser": "on",
            "groups": self.group.pk, "user_permissions": self.permission.pk,
        }.items():
            with self.subTest(field=field):
                response = self.client.post(url, self.user_form(self.target, **{field: value}))
                self.assertEqual(response.status_code, 403)
                self.target.refresh_from_db()
                self.assertEqual(self.target.first_name, "")
                self.assertFalse(self.target.is_staff)
                self.assertFalse(self.target.is_superuser)
                self.assertFalse(self.target.groups.exists())
                self.assertFalse(self.target.user_permissions.exists())
        self.assertEqual(self.client.post(url, self.user_form(self.target)).status_code, 302)
        self.target.refresh_from_db()
        self.assertEqual(self.target.first_name, "Updated")

    def test_user_admin_rejects_privilege_injection_on_create(self):
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="missions", codename="add_user",
        ))
        self.client.force_login(self.staff)
        url = reverse("admin:missions_user_add")
        self.assertEqual(self.client.post(url, {"username": "injected", "is_superuser": "on"}).status_code, 403)
        self.assertFalse(User.objects.filter(username="injected").exists())

    def test_user_admin_protects_other_privileged_accounts(self):
        self.client.force_login(self.staff)
        url = reverse("admin:missions_user_change", args=[self.root.pk])
        self.assertEqual(self.client.post(url, self.user_form(self.root, password="replacement")).status_code, 403)
        self.root.refresh_from_db()
        self.assertNotEqual(self.root.password, "replacement")

    def test_superuser_can_edit_admin_privileges(self):
        self.client.force_login(self.root)
        url = reverse("admin:missions_user_change", args=[self.target.pk])
        response = self.client.post(url, self.user_form(
            self.target, is_staff="on", is_superuser="on",
            groups=self.group.pk, user_permissions=self.permission.pk,
        ))
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_staff and self.target.is_superuser)
        self.assertEqual(list(self.target.groups.all()), [self.group])
        self.assertEqual(list(self.target.user_permissions.all()), [self.permission])

    def test_group_admin_blocks_permission_injection_but_allows_rename(self):
        self.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="auth", codename="change_group",
        ))
        self.group.user_set.add(self.staff)
        self.client.force_login(self.staff)
        url = reverse("admin:auth_group_change", args=[self.group.pk])
        self.assertEqual(self.client.post(url, {
            "name": "Renamed", "permissions": self.permission.pk,
        }).status_code, 403)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "fixture group")
        self.assertFalse(self.group.permissions.exists())
        self.assertEqual(self.client.post(url, {"name": "Renamed"}).status_code, 302)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Renamed")
        self.client.force_login(self.root)
        self.assertEqual(self.client.post(url, {
            "name": "Renamed", "permissions": self.permission.pk,
        }).status_code, 302)
        self.assertEqual(list(self.group.permissions.all()), [self.permission])
