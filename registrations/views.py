
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from events.models import Event

from .forms import AttendeeRegistrationForm, TicketLookupForm
from .qr import generate_ticket_qr
from .models import Registration
from .services import RegistrationError, register_attendee


CAPACITY_STATUSES = [
    Registration.Status.CONFIRMED,
    Registration.Status.CHECKED_IN,
]


@never_cache
@require_http_methods(["GET", "POST"])
def event_registration(request, event_id):
    event = get_object_or_404(
        Event,
        pk=event_id,
        status=Event.Status.PUBLISHED,
    )

    registered_count = Registration.objects.filter(
        event=event,
        status__in=CAPACITY_STATUSES,
    ).count()

    spots_left = max(event.capacity - registered_count, 0)

    # Prevent displaying the form for closed or full events.
    if request.method == "GET":
        if event.starts_at <= timezone.now() or spots_left == 0:
            return redirect("events:detail", pk=event.pk)

    form = AttendeeRegistrationForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            registration = register_attendee(
                event_id=event.pk,
                full_name=form.cleaned_data["full_name"],
                email=form.cleaned_data["email"],
                mobile=form.cleaned_data["mobile"],
            )

        except RegistrationError as error:
            form.add_error(None, str(error))

        except ValidationError as error:
            form.add_error(None, " ".join(error.messages))

        else:
            # Only this browser session can view this confirmation.
            request.session["new_registration_id"] = registration.pk

            return redirect("registrations:confirmation")

    return render(
        request,
        "registrations/registration_form.html",
        {
            "event": event,
            "form": form,
            "spots_left": spots_left,
        },
    )


@never_cache
@require_GET
def registration_confirmation(request):
    registration_id = request.session.get(
        "new_registration_id"
    )

    if not registration_id:
        return redirect("events:list")

    registration = (
        Registration.objects.select_related("event")
        .filter(pk=registration_id)
        .first()
    )

    if registration is None:
        return redirect("events:list")


    return render(
        request,
        "registrations/confirmation.html",
        {
            "registration": registration,
            "qr_code_data": generate_ticket_qr(
                registration.ticket_code
            ),
        },
    )


@never_cache
@require_http_methods(["GET", "POST"])
def ticket_lookup(request):
    form = TicketLookupForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST":
        # Revoke access to any previously viewed ticket
        # before processing a new lookup.
        request.session.pop("new_registration_id", None)

        if form.is_valid():
            ticket_code = form.cleaned_data["ticket_code"]
            email = form.cleaned_data["email"]

            registration = Registration.objects.filter(
                ticket_code=ticket_code,
                email__iexact=email,
            ).first()

            if registration is None:
                form.add_error(
                    None,
                    "Ticket not found",
                )
            else:
                request.session[
                    "new_registration_id"
                ] = registration.pk

                return redirect(
                    "registrations:confirmation"
                )

    return render(
        request,
        "registrations/ticket_lookup.html",
        {"form": form},
    )

