
from dataclasses import dataclass

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from registrations.models import Registration


@dataclass(frozen=True)
class CheckInResult:
    status: str
    registration: Registration | None = None


def check_in_ticket(*, event, ticket_code, staff_user):
    """
    Validate a ticket and record a single check-in.

    Check-in is permitted only on the event's
    scheduled date in Asia/Manila.
    """

    if (
        not staff_user.is_authenticated
        or not staff_user.is_active
        or not staff_user.is_staff
    ):
        raise PermissionDenied(
            "Staff authorization is required."
        )

    event_date = timezone.localtime(
        event.starts_at
    ).date()

    if timezone.localdate() != event_date:
        return CheckInResult(status="wrong_day")

    normalized_code = ticket_code.strip().upper()

    registration = Registration.objects.filter(
        event=event,
        ticket_code=normalized_code,
    ).first()

    if registration is None:
        return CheckInResult(status="invalid_ticket")

    if registration.status == Registration.Status.CHECKED_IN:
        return CheckInResult(
            status="already_checked_in",
            registration=registration,
        )

    if registration.status != Registration.Status.CONFIRMED:
        return CheckInResult(status="invalid_ticket")

    # Conditional database update prevents the same
    # ticket from being checked in twice.
    updated = Registration.objects.filter(
        pk=registration.pk,
        status=Registration.Status.CONFIRMED,
        checked_in_at__isnull=True,
    ).update(
        status=Registration.Status.CHECKED_IN,
        checked_in_at=timezone.now(),
        checked_in_by=staff_user,
    )

    registration.refresh_from_db()

    if updated == 1:
        return CheckInResult(
            status="checked_in",
            registration=registration,
        )

    if registration.status == Registration.Status.CHECKED_IN:
        return CheckInResult(
            status="already_checked_in",
            registration=registration,
        )

    return CheckInResult(status="invalid_ticket")
