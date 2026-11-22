
import base64
from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from registrations.models import Registration


class TicketTests(TestCase):

    def setUp(self):
        start = timezone.now() + timedelta(days=5)

        event = Event.objects.create(
            title="Cebu Dev Meetup 2026",
            description="A developer meetup.",
            venue="Ayala Center Cebu",
            starts_at=start,
            ends_at=start + timedelta(hours=3),
            capacity=30,
            status=Event.Status.PUBLISHED,
        )

        self.registration = Registration.objects.create(
            event=event,
            full_name="Ana Cruz",
            email="ana@example.com",
            mobile="09171234567",
        )

        self.lookup_url = reverse("registrations:lookup")
        self.ticket_url = reverse(
            "registrations:confirmation"
        )

    def authorize_ticket(self):
        session = self.client.session
        session["new_registration_id"] = self.registration.pk
        session.save()

    def test_ticket_contains_valid_png_qr(self):
        self.authorize_ticket()

        response = self.client.get(self.ticket_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.registration.ticket_code,
        )

        qr_data = response.context["qr_code_data"]

        self.assertTrue(
            qr_data.startswith("data:image/png;base64,")
        )

        png_bytes = base64.b64decode(
            qr_data.split(",", 1)[1]
        )

        self.assertTrue(
            png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        )

    def test_successful_ticket_lookup(self):
        response = self.client.post(
            self.lookup_url,
            {
                "ticket_code": self.registration.ticket_code.lower(),
                "email": "ANA@EXAMPLE.COM",
            },
        )

        self.assertRedirects(response, self.ticket_url)

        ticket_response = self.client.get(self.ticket_url)

        self.assertContains(ticket_response, "Ana Cruz")
        self.assertContains(
            ticket_response,
            self.registration.ticket_code,
        )

    def test_wrong_ticket_code_does_not_reveal_details(self):
        response = self.client.post(
            self.lookup_url,
            {
                "ticket_code": "EP-INVALID",
                "email": "ana@example.com",
            },
        )

        self.assertContains(response, "Ticket not found")
        self.assertNotContains(response, "Ana Cruz")

    def test_wrong_email_does_not_reveal_details(self):
        response = self.client.post(
            self.lookup_url,
            {
                "ticket_code": self.registration.ticket_code,
                "email": "wrong@example.com",
            },
        )

        self.assertContains(response, "Ticket not found")
        self.assertNotContains(response, "Ana Cruz")

    def test_ticket_requires_authorized_session(self):
        another_client = Client()

        response = another_client.get(self.ticket_url)

        self.assertRedirects(
            response,
            reverse("events:list"),
        )

    def test_failed_lookup_revokes_previous_ticket_access(self):
        self.authorize_ticket()

        self.client.post(
            self.lookup_url,
            {
                "ticket_code": "EP-INVALID",
                "email": "ana@example.com",
            },
        )

        response = self.client.get(self.ticket_url)

        self.assertRedirects(
            response,
            reverse("events:list"),
        )
