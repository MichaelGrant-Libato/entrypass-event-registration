
import re
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from events.models import Event
from .models import Registration


class RegistrationModelTests(TestCase):

    def setUp(self):
        start = timezone.now() + timedelta(days=7)

        self.event = Event.objects.create(
            title="Cebu Dev Meetup 2026",
            description="A meetup for Cebu developers.",
            venue="Ayala Center Cebu, Function Room 2",
            starts_at=start,
            ends_at=start + timedelta(hours=3),
            capacity=30,
            status=Event.Status.PUBLISHED,
        )

    def create_registration(self, email="ana@example.com"):
        return Registration.objects.create(
            event=self.event,
            full_name="Ana Cruz",
            email=email,
            mobile="09171234567",
        )

    def test_registration_is_created(self):
        registration = self.create_registration()

        self.assertEqual(registration.event, self.event)
        self.assertEqual(
            registration.status,
            Registration.Status.CONFIRMED,
        )
        self.assertIsNotNone(registration.registered_at)

    def test_ticket_codes_are_unique(self):
        first = self.create_registration()
        second = self.create_registration("ben@example.com")

        self.assertNotEqual(
            first.ticket_code,
            second.ticket_code,
        )

        self.assertTrue(
            re.fullmatch(
                r"EP-[0-9A-F]{32}",
                first.ticket_code,
            )
        )

    def test_email_is_normalized(self):
        registration = self.create_registration(
            "ANA@EXAMPLE.COM"
        )

        self.assertEqual(
            registration.email,
            "ana@example.com",
        )

    def test_invalid_mobile_numbers(self):
        invalid_numbers = [
            "0917123456",
            "08171234567",
            "091712345678",
        ]

        for mobile in invalid_numbers:
            with self.subTest(mobile=mobile):
                registration = Registration(
                    event=self.event,
                    full_name="Ana Cruz",
                    email="ana@example.com",
                    mobile=mobile,
                )

                with self.assertRaises(ValidationError):
                    registration.full_clean()

    def test_invalid_email(self):
        registration = Registration(
            event=self.event,
            full_name="Ana Cruz",
            email="invalid-email",
            mobile="09171234567",
        )

        with self.assertRaises(ValidationError):
            registration.full_clean()

    def test_duplicate_email_is_blocked(self):
        self.create_registration()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_registration("ANA@example.com")

    def test_same_email_allowed_for_different_events(self):
        self.create_registration()

        second_event = Event.objects.create(
            title="Cebu Tech Workshop",
            description="A software development workshop.",
            venue="Cebu IT Park",
            starts_at=self.event.starts_at + timedelta(days=1),
            ends_at=self.event.ends_at + timedelta(days=1),
            capacity=20,
            status=Event.Status.PUBLISHED,
        )

        second_registration = Registration.objects.create(
            event=second_event,
            full_name="Ana Cruz",
            email="ana@example.com",
            mobile="09171234567",
        )

        self.assertEqual(
            second_registration.event,
            second_event,
        )

    def test_cancelled_attendee_can_register_again(self):
        registration = self.create_registration()

        registration.status = Registration.Status.CANCELLED
        registration.save(update_fields=["status"])

        new_registration = self.create_registration()

        self.assertNotEqual(
            registration.ticket_code,
            new_registration.ticket_code,
        )
        self.assertEqual(
            new_registration.status,
            Registration.Status.CONFIRMED,
        )

    def test_waitlisted_email_cannot_register_twice(self):
        registration = self.create_registration()
        registration.status = Registration.Status.WAITLISTED
        registration.save(update_fields=["status"])

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_registration()
