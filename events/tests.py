
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Event


class EventModelTests(TestCase):

    def setUp(self):
        self.start = timezone.now() + timedelta(days=7)

        self.event = Event(
            title="Cebu Dev Meetup 2026",
            description="A meetup for Cebu developers.",
            venue="Ayala Center Cebu",
            starts_at=self.start,
            ends_at=self.start + timedelta(hours=3),
            capacity=30,
        )

    def test_event_is_valid(self):
        self.event.full_clean()
        self.event.save()

        self.assertEqual(self.event.capacity, 30)
        self.assertEqual(
            self.event.status,
            Event.Status.DRAFT
        )

    def test_end_time_must_be_after_start(self):
        self.event.ends_at = (
            self.start - timedelta(hours=1)
        )

        with self.assertRaises(ValidationError):
            self.event.full_clean()

    def test_capacity_cannot_be_zero(self):
        self.event.capacity = 0

        with self.assertRaises(ValidationError):
            self.event.full_clean()
