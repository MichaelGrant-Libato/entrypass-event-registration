
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class StaffAuthenticationTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.staff = User.objects.create_user(
            username="doorstaff",
            password="TestPassword123!",
            is_staff=True,
        )

        self.attendee = User.objects.create_user(
            username="attendee",
            password="AttendeePassword123!",
        )

        self.login_url = reverse("checkin:login")
        self.dashboard_url = reverse("checkin:dashboard")
        self.logout_url = reverse("checkin:logout")

    def test_staff_can_sign_in(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "doorstaff",
                "password": "TestPassword123!",
            },
        )

        self.assertRedirects(
            response,
            self.dashboard_url,
        )

    def test_anonymous_user_cannot_access_dashboard(self):
        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            self.login_url,
            response["Location"],
        )

    def test_regular_user_cannot_access_dashboard(self):
        self.client.force_login(self.attendee)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 302)

    def test_regular_user_cannot_sign_in_as_staff(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "attendee",
                "password": "AttendeePassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.client.session.get("_auth_user_id")
        )

    def test_staff_can_sign_out(self):
        self.client.force_login(self.staff)

        response = self.client.post(self.logout_url)

        self.assertRedirects(
            response,
            self.login_url,
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_password_is_hashed(self):
        self.assertNotEqual(
            self.staff.password,
            "TestPassword123!",
        )

        self.assertTrue(
            self.staff.check_password("TestPassword123!")
        )
