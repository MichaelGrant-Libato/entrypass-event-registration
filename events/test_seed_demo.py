
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from events.models import Event
from registrations.models import Registration


class SeedDemoTests(TestCase):

    def test_seed_creates_full_event_without_duplicates(self):
        call_command(
            "seed_demo",
            stdout=StringIO(),
        )

        full_event = Event.objects.get(
            title="EntryPass Demo - Fully Booked"
        )

        self.assertEqual(full_event.capacity, 3)

        self.assertEqual(
            Registration.objects.filter(
                event=full_event,
                status=Registration.Status.CONFIRMED,
            ).count(),
            3,
        )

        # Running twice must not create duplicate attendees.
        call_command(
            "seed_demo",
            stdout=StringIO(),
        )

        self.assertEqual(
            Registration.objects.filter(
                event=full_event
            ).count(),
            3,
        )

    def test_seed_creates_todays_checkin_event(self):
        call_command(
            "seed_demo",
            stdout=StringIO(),
        )

        today = timezone.localdate()

        event = Event.objects.get(
            title=(
                "EntryPass Door Demo - "
                f"{today.isoformat()}"
            )
        )

        self.assertEqual(
            timezone.localtime(
                event.starts_at
            ).date(),
            today,
        )

        self.assertTrue(
            Registration.objects.filter(
                event=event,
                email="visitor.demo@example.com",
            ).exists()
        )
