
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from events.models import Event
from registrations.models import Registration
from registrations.services import (
    RegistrationError,
    register_attendee,
)


class RegistrationServiceTests(TestCase):

    def setUp(self):
        start = timezone.now() + timedelta(days=7)

        self.event = Event.objects.create(
            title="Cebu Dev Meetup 2026",
            description="A developer meetup in Cebu.",
            venue="Ayala Center Cebu, Function Room 2",
            starts_at=start,
            ends_at=start + timedelta(hours=3),
            capacity=2,
            status=Event.Status.PUBLISHED,
        )

    def register(self, email="ana@example.com", mobile="09171234567"):
        return register_attendee(
            event_id=self.event.pk,
            full_name="Ana Cruz",
            email=email,
            mobile=mobile,
        )

    def test_successful_registration(self):
        registration = self.register()

        self.assertEqual(
            registration.status,
            Registration.Status.CONFIRMED,
        )
        self.assertTrue(registration.ticket_code)
        self.assertEqual(Registration.objects.count(), 1)

    def test_duplicate_registration_is_blocked(self):
        self.register()

        with self.assertRaises(RegistrationError) as error:
            self.register(email="ANA@EXAMPLE.COM")

        self.assertEqual(error.exception.code, "duplicate")
        self.assertEqual(Registration.objects.count(), 1)

    def test_event_capacity_is_enforced(self):
        self.event.capacity = 1
        self.event.save(update_fields=["capacity"])

        self.register()

        with self.assertRaises(RegistrationError) as error:
            self.register(email="ben@example.com")

        self.assertEqual(error.exception.code, "full")
        self.assertEqual(Registration.objects.count(), 1)

    def test_cancelled_registration_frees_capacity(self):
        self.event.capacity = 1
        self.event.save(update_fields=["capacity"])

        first = self.register()
        first.status = Registration.Status.CANCELLED
        first.save(update_fields=["status"])

        second = self.register(email="ben@example.com")

        self.assertEqual(
            second.status,
            Registration.Status.CONFIRMED,
        )

    def test_checked_in_attendee_counts_towards_capacity(self):
        self.event.capacity = 1
        self.event.save(update_fields=["capacity"])

        first = self.register()
        first.status = Registration.Status.CHECKED_IN
        first.save(update_fields=["status"])

        with self.assertRaises(RegistrationError) as error:
            self.register(email="ben@example.com")

        self.assertEqual(error.exception.code, "full")

    def test_draft_event_rejects_registration(self):
        self.event.status = Event.Status.DRAFT
        self.event.save(update_fields=["status"])

        with self.assertRaises(RegistrationError) as error:
            self.register()

        self.assertEqual(error.exception.code, "unavailable")

    def test_started_event_rejects_registration(self):
        self.event.starts_at = timezone.now() - timedelta(hours=1)
        self.event.ends_at = timezone.now() + timedelta(hours=2)
        self.event.save(update_fields=["starts_at", "ends_at"])

        with self.assertRaises(RegistrationError) as error:
            self.register()

        self.assertEqual(error.exception.code, "ended")

    def test_invalid_mobile_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.register(mobile="12345")

        self.assertEqual(Registration.objects.count(), 0)

    def test_nonexistent_event_is_rejected(self):
        with self.assertRaises(RegistrationError) as error:
            register_attendee(
                event_id=999999,
                full_name="Ana Cruz",
                email="ana@example.com",
                mobile="09171234567",
            )

        self.assertEqual(error.exception.code, "not_found")
