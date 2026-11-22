
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from registrations.models import Registration


class AttendeeRegistrationViewTests(TestCase):

    def setUp(self):
        start = timezone.now() + timedelta(days=5)

        self.event = Event.objects.create(
            title="Cebu Dev Meetup 2026",
            description="A community meetup for developers.",
            venue="Ayala Center Cebu, Function Room 2",
            starts_at=start,
            ends_at=start + timedelta(hours=3),
            capacity=2,
            status=Event.Status.PUBLISHED,
        )

        self.url = reverse(
            "registrations:register",
            args=[self.event.pk],
        )

        self.valid_data = {
            "full_name": "Ana Cruz",
            "email": "ana@example.com",
            "mobile": "09171234567",
        }

    def test_registration_page_loads(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "registrations/registration_form.html",
        )
        self.assertContains(response, "Reserve your spot")

    def test_successful_registration(self):
        response = self.client.post(
            self.url,
            data=self.valid_data,
        )

        self.assertRedirects(
            response,
            reverse("registrations:confirmation"),
        )

        registration = Registration.objects.get()

        self.assertEqual(
            registration.status,
            Registration.Status.CONFIRMED,
        )

        confirmation = self.client.get(
            reverse("registrations:confirmation")
        )

        self.assertContains(
            confirmation,
            registration.ticket_code,
        )

    def test_invalid_information(self):
        data = {
            **self.valid_data,
            "email": "invalid-email",
            "mobile": "12345",
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertIn("mobile", response.context["form"].errors)
        self.assertEqual(Registration.objects.count(), 0)

    def test_duplicate_registration(self):
        self.client.post(self.url, data=self.valid_data)

        response = self.client.post(
            self.url,
            data={
                **self.valid_data,
                "email": "ANA@EXAMPLE.COM",
            },
        )

        self.assertContains(
            response,
            "This email is already registered",
        )
        self.assertEqual(Registration.objects.count(), 1)

    def test_full_event_blocks_registration(self):
        self.event.capacity = 1
        self.event.save(update_fields=["capacity"])

        self.client.post(self.url, data=self.valid_data)

        get_response = self.client.get(self.url)

        self.assertRedirects(
            get_response,
            reverse("events:detail", args=[self.event.pk]),
        )

        post_response = self.client.post(
            self.url,
            data={
                **self.valid_data,
                "email": "ben@example.com",
            },
        )

        self.assertContains(
            post_response,
            "This event is already full",
        )
        self.assertEqual(Registration.objects.count(), 1)

    def test_confirmation_requires_session(self):
        response = self.client.get(
            reverse("registrations:confirmation")
        )

        self.assertRedirects(
            response,
            reverse("events:list"),
        )

    def test_draft_event_cannot_be_registered(self):
        self.event.status = Event.Status.DRAFT
        self.event.save(update_fields=["status"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
