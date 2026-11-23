
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from registrations.models import Registration


class AttendeeManagementTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.staff = User.objects.create_user(
            username="staff_manager",
            password="TestPassword123!",
            is_staff=True,
        )

        self.regular_user = User.objects.create_user(
            username="regular_user",
            password="TestPassword123!",
        )

        start = timezone.now() + timedelta(days=5)

        self.event = Event.objects.create(
            title="Cebu Dev Meetup",
            description="Test event",
            venue="Cebu",
            starts_at=start,
            ends_at=start + timedelta(hours=3),
            capacity=5,
            status=Event.Status.PUBLISHED,
        )

        self.confirmed = Registration.objects.create(
            event=self.event,
            full_name="Ana Cruz",
            email="ana@example.com",
            mobile="09171234567",
        )

        self.checked_in = Registration.objects.create(
            event=self.event,
            full_name="Ben Santos",
            email="ben@example.com",
            mobile="09181234567",
            status=Registration.Status.CHECKED_IN,
            checked_in_at=timezone.now(),
            checked_in_by=self.staff,
        )

        self.cancelled = Registration.objects.create(
            event=self.event,
            full_name="Carla Reyes",
            email="carla@example.com",
            mobile="09191234567",
            status=Registration.Status.CANCELLED,
        )

        self.other_event = Event.objects.create(
            title="Other Event",
            description="Different event",
            venue="Other Venue",
            starts_at=start,
            ends_at=start + timedelta(hours=2),
            capacity=10,
            status=Event.Status.PUBLISHED,
        )

        self.other_registration = Registration.objects.create(
            event=self.other_event,
            full_name="Daniel Other",
            email="daniel@example.com",
            mobile="09161234567",
        )

        self.url = reverse(
            "checkin:event_attendees",
            args=[self.event.pk],
        )

        self.client.force_login(self.staff)

    def test_staff_can_view_attendee_directory(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Attendee directory")
        self.assertContains(response, "Ana Cruz")
        self.assertContains(response, "Ben Santos")
        self.assertContains(response, "Carla Reyes")

    def test_statistics_exclude_cancelled_attendees(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.context["registered_count"], 2
        )

        self.assertEqual(
            response.context["checked_in_count"], 1
        )

        self.assertEqual(
            response.context["spots_left"], 3
        )

    def test_search_by_name_is_case_insensitive(self):
        response = self.client.get(
            self.url, {"q": "ana"}
        )

        self.assertContains(response, "Ana Cruz")
        self.assertNotContains(response, "Ben Santos")
        self.assertEqual(
            response.context["page_obj"].paginator.count, 1
        )

        # Statistics still represent the whole event.
        self.assertEqual(
            response.context["registered_count"], 2
        )

    def test_search_by_ticket_code(self):
        response = self.client.get(
            self.url,
            {"q": self.checked_in.ticket_code.lower()},
        )

        self.assertContains(response, "Ben Santos")
        self.assertNotContains(response, "Ana Cruz")

    def test_other_event_attendees_are_not_exposed(self):
        response = self.client.get(self.url)

        self.assertNotContains(response, "Daniel Other")

        response = self.client.get(
            self.url,
            {"q": self.other_registration.ticket_code},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count, 0
        )

    def test_nonstaff_cannot_view_directory(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_pagination(self):
        for index in range(9):
            Registration.objects.create(
                event=self.event,
                full_name=f"Visitor {index}",
                email=f"visitor{index}@example.com",
                mobile=f"0917{index:07d}",
            )

        first_page = self.client.get(self.url)

        self.assertEqual(
            first_page.context["page_obj"].paginator.num_pages,
            2,
        )

        second_page = self.client.get(
            self.url, {"page": 2}
        )

        self.assertEqual(
            second_page.context["page_obj"].number, 2
        )

    def test_unknown_event_returns_404(self):
        url = reverse(
            "checkin:event_attendees",
            args=[999999],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
