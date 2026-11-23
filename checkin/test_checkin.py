
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from registrations.models import Registration
from checkin.services import check_in_ticket


class TicketCheckInTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.staff = User.objects.create_user(
            username="checkin_staff",
            password="TestPassword123!",
            is_staff=True,
        )

        self.regular_user = User.objects.create_user(
            username="regular_user",
            password="TestPassword123!",
        )

        start = timezone.localtime().replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0,
        )

        self.event = Event.objects.create(
            title="EntryPass Test Event",
            description="Check-in tests",
            venue="Test Venue",
            starts_at=start,
            ends_at=start + timedelta(hours=8),
            capacity=30,
            status=Event.Status.PUBLISHED,
        )

        self.registration = Registration.objects.create(
            event=self.event,
            full_name="Ana Cruz",
            email="ana@example.com",
            mobile="09171234567",
        )

        self.url = reverse(
            "checkin:event_checkin",
            args=[self.event.pk],
        )

        self.client.force_login(self.staff)

    def submit_ticket(self, code=None):
        return self.client.post(
            self.url,
            {
                "ticket_code": (
                    code
                    if code is not None
                    else self.registration.ticket_code
                ),
            },
        )

    def test_staff_can_open_checkin_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verify a ticket")

    def test_successful_checkin(self):
        response = self.submit_ticket()

        self.assertContains(response, "Checked in")

        self.registration.refresh_from_db()

        self.assertEqual(
            self.registration.status,
            Registration.Status.CHECKED_IN,
        )

        self.assertIsNotNone(
            self.registration.checked_in_at
        )

        self.assertEqual(
            self.registration.checked_in_by,
            self.staff,
        )

    def test_duplicate_checkin_preserves_timestamp(self):
        self.submit_ticket()

        self.registration.refresh_from_db()
        original_time = self.registration.checked_in_at

        response = self.submit_ticket()

        self.assertContains(
            response,
            "Already checked in",
        )

        self.registration.refresh_from_db()

        self.assertEqual(
            self.registration.checked_in_at,
            original_time,
        )

    def test_invalid_ticket(self):
        response = self.submit_ticket("EP-INVALID")

        self.assertContains(response, "Invalid ticket")

        self.registration.refresh_from_db()

        self.assertEqual(
            self.registration.status,
            Registration.Status.CONFIRMED,
        )

    def test_ticket_from_another_event_is_invalid(self):
        other_event = Event.objects.create(
            title="Other Event",
            description="Separate event",
            venue="Other Venue",
            starts_at=self.event.starts_at,
            ends_at=self.event.ends_at,
            capacity=10,
            status=Event.Status.PUBLISHED,
        )

        other_registration = Registration.objects.create(
            event=other_event,
            full_name="Ben Santos",
            email="ben@example.com",
            mobile="09181234567",
        )

        response = self.submit_ticket(
            other_registration.ticket_code
        )

        self.assertContains(response, "Invalid ticket")
        self.assertNotContains(response, "Ben Santos")

        other_registration.refresh_from_db()

        self.assertEqual(
            other_registration.status,
            Registration.Status.CONFIRMED,
        )

    def test_cancelled_ticket_is_invalid(self):
        self.registration.status = (
            Registration.Status.CANCELLED
        )
        self.registration.save(update_fields=["status"])

        response = self.submit_ticket()

        self.assertContains(response, "Invalid ticket")

    def test_checkin_blocked_before_event_day(self):
        self.event.starts_at += timedelta(days=1)
        self.event.ends_at += timedelta(days=1)
        self.event.save(
            update_fields=["starts_at", "ends_at"]
        )

        response = self.submit_ticket()

        self.assertContains(
            response,
            "Check-in unavailable",
        )

        self.registration.refresh_from_db()
        self.assertIsNone(
            self.registration.checked_in_at
        )

    def test_nonstaff_cannot_checkin(self):
        self.client.force_login(self.regular_user)

        response = self.submit_ticket()

        self.assertEqual(response.status_code, 302)

        self.registration.refresh_from_db()
        self.assertIsNone(
            self.registration.checked_in_at
        )

        with self.assertRaises(PermissionDenied):
            check_in_ticket(
                event=self.event,
                ticket_code=self.registration.ticket_code,
                staff_user=self.regular_user,
            )
