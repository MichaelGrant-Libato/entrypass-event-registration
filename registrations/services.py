
from django.db import IntegrityError, transaction
from django.utils import timezone

from events.models import Event
from .models import Registration


ACTIVE_STATUSES = [
    Registration.Status.CONFIRMED,
    Registration.Status.CHECKED_IN,
    Registration.Status.WAITLISTED,
]

CAPACITY_STATUSES = [
    Registration.Status.CONFIRMED,
    Registration.Status.CHECKED_IN,
]


class RegistrationError(Exception):
    """A registration rule that prevents an attendee from signing up."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def register_attendee(*, event_id, full_name, email, mobile):
    """
    Validate and create an attendee registration.

    Raises:
        RegistrationError: Event unavailable, duplicate, or full.
        ValidationError: Invalid attendee information.
    """
    normalized_email = email.strip().lower()

    try:
        with transaction.atomic():
            try:
                event = Event.objects.select_for_update().get(
                    pk=event_id
                )
            except Event.DoesNotExist:
                raise RegistrationError(
                    "not_found",
                    "This event could not be found.",
                )

            if event.status != Event.Status.PUBLISHED:
                raise RegistrationError(
                    "unavailable",
                    "Registration is not open for this event.",
                )

            if event.starts_at <= timezone.now():
                raise RegistrationError(
                    "ended",
                    "Registration for this event has closed.",
                )

            has_registration = Registration.objects.filter(
                event=event,
                email__iexact=normalized_email,
                status__in=ACTIVE_STATUSES,
            ).exists()

            if has_registration:
                raise RegistrationError(
                    "duplicate",
                    "This email is already registered for the event.",
                )

            registered_count = Registration.objects.filter(
                event=event,
                status__in=CAPACITY_STATUSES,
            ).count()

            if registered_count >= event.capacity:
                raise RegistrationError(
                    "full",
                    "This event is already full.",
                )

            registration = Registration(
                event=event,
                full_name=full_name.strip(),
                email=normalized_email,
                mobile=mobile.strip(),
            )

            registration.full_clean()
            registration.save()

            return registration

    except IntegrityError:
        # The transaction has already rolled back here.
        # Translate only a real duplicate into a friendly error.
        if Registration.objects.filter(
            event_id=event_id,
            email__iexact=normalized_email,
            status__in=ACTIVE_STATUSES,
        ).exists():
            raise RegistrationError(
                "duplicate",
                "This email is already registered for the event.",
            ) from None

        # Unexpected database errors should not be hidden.
        raise
