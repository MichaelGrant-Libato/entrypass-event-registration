
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from registrations.models import Registration
from .models import Event


def events_with_counts():
    """Include confirmed attendance counts in event queries."""
    return Event.objects.annotate(
        registered_count=Count(
            "registrations",
            filter=Q(
                registrations__status__in=[
                    Registration.Status.CONFIRMED,
                    Registration.Status.CHECKED_IN,
                ]
            ),
        )
    )


def prepare_event(event, now):
    """Add availability information for presentation."""
    event.spots_left = max(
        event.capacity - event.registered_count, 0
    )
    event.has_started = event.starts_at <= now
    event.has_ended = event.ends_at <= now
    event.registration_open = (
        not event.has_started and event.spots_left > 0
    )
    return event


def event_list(request):
    now = timezone.now()

    events = list(
        events_with_counts()
        .filter(
            status=Event.Status.PUBLISHED,
            starts_at__gt=now,
        )
        .order_by("starts_at")
    )

    events = [prepare_event(event, now) for event in events]

    return render(
        request,
        "events/event_list.html",
        {"events": events},
    )


def event_detail(request, pk):
    now = timezone.now()

    event = get_object_or_404(
        events_with_counts(),
        pk=pk,
        status=Event.Status.PUBLISHED,
    )

    prepare_event(event, now)

    return render(
        request,
        "events/event_detail.html",
        {"event": event},
    )
