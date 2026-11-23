
import os
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from events.models import Event
from registrations.models import Registration


def local_datetime(year, month, day, hour, minute=0):
    return timezone.make_aware(
        datetime(year, month, day, hour, minute)
    )


def add_attendee(event, name, email, mobile):
    registration, created = Registration.objects.get_or_create(
        event=event,
        email=email,
        defaults={
            "full_name": name,
            "mobile": mobile,
            "status": Registration.Status.CONFIRMED,
        },
    )
    return registration


class Command(BaseCommand):
    help = "Create non-destructive demo data for EntryPass."

    @transaction.atomic
    def handle(self, *args, **options):
        # Event 1: Upcoming event with open registration.
        meetup, _ = Event.objects.get_or_create(
            title="Cebu Dev Meetup 2026",
            defaults={
                "description": (
                    "A community meetup for developers "
                    "and technology enthusiasts in Cebu."
                ),
                "venue": "Ayala Center Cebu, Function Room 2",
                "starts_at": local_datetime(
                    2026, 12, 6, 6
                ),
                "ends_at": local_datetime(
                    2026, 12, 6, 12
                ),
                "capacity": 30,
                "status": Event.Status.PUBLISHED,
            },
        )

        add_attendee(
            meetup,
            "Ana Demo",
            "ana.demo@example.com",
            "09170000001",
        )

        # Event 2: Full event for capacity testing.
        full_event, _ = Event.objects.get_or_create(
            title="EntryPass Demo - Fully Booked",
            defaults={
                "description": (
                    "A sample workshop demonstrating "
                    "the fully booked registration state."
                ),
                "venue": "Cebu IT Park, Demo Room",
                "starts_at": local_datetime(
                    2026, 12, 8, 9
                ),
                "ends_at": local_datetime(
                    2026, 12, 8, 12
                ),
                "capacity": 3,
                "status": Event.Status.PUBLISHED,
            },
        )

        if full_event.capacity != 3:
            raise CommandError(
                "The demo full event must have capacity 3."
            )

        existing_emails = {
            registration.email
            for registration in Registration.objects.filter(
                event=full_event,
            )
        }

        expected_emails = {
            f"full{number}@example.com"
            for number in range(1, 4)
        }

        if existing_emails - expected_emails:
            raise CommandError(
                "The demo full event contains additional "
                "registrations. Inspect it before seeding."
            )

        for number in range(1, 4):
            add_attendee(
                full_event,
                f"Demo Attendee {number}",
                f"full{number}@example.com",
                f"0917{number:07d}",
            )

        active_count = Registration.objects.filter(
            event=full_event,
            status__in=[
                Registration.Status.CONFIRMED,
                Registration.Status.CHECKED_IN,
            ],
        ).count()

        if active_count != full_event.capacity:
            raise CommandError(
                "The demo full event is not fully booked. "
                "Inspect existing registration statuses."
            )

        # Event 3: Today's event for check-in demonstrations.
        today = timezone.localdate()

        door_event, _ = Event.objects.get_or_create(
            title=(
                "EntryPass Door Demo - "
                f"{today.isoformat()}"
            ),
            defaults={
                "description": (
                    "Local demonstration of staff ticket "
                    "verification and attendance."
                ),
                "venue": "EntryPass Demo Venue",
                "starts_at": timezone.make_aware(
                    datetime.combine(today, time(9, 0))
                ),
                "ends_at": timezone.make_aware(
                    datetime.combine(today, time(22, 0))
                ),
                "capacity": 10,
                "status": Event.Status.PUBLISHED,
            },
        )

        demo_ticket = add_attendee(
            door_event,
            "Demo Visitor",
            "visitor.demo@example.com",
            "09170000101",
        )

        # Optional demo staff account.
        username = os.getenv(
            "DEMO_STAFF_USERNAME",
            "entrypass_demo",
        ).strip()

        password = os.getenv("DEMO_STAFF_PASSWORD", "")

        if password:
            if len(password) < 12:
                raise CommandError(
                    "Demo staff password must be at least "
                    "12 characters."
                )

            User = get_user_model()

            if not User.objects.filter(
                username=username
            ).exists():
                User.objects.create_user(
                    username=username,
                    password=password,
                    is_staff=True,
                    is_superuser=False,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        "Created demo staff account."
                    )
                )
            else:
                self.stdout.write(
                    "Demo staff already exists; "
                    "credentials were not changed."
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "DEMO_STAFF_PASSWORD not set. "
                    "Skipping demo staff creation."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo event data is ready."
            )
        )
        self.stdout.write(
            f"Open event: {meetup.title}"
        )
        self.stdout.write(
            f"Full event: {full_event.title}"
        )
        self.stdout.write(
            f"Door demo event ID: {door_event.pk}"
        )
        self.stdout.write(
            f"Door demo ticket: {demo_ticket.ticket_code}"
        )
