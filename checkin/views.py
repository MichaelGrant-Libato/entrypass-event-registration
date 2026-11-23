
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import TicketCheckInForm
from .services import check_in_ticket

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.views.decorators.http import require_GET

from registrations.models import Registration

from events.models import Event


def staff_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url="checkin:login",
    )(view_func)


@never_cache
@staff_required
def dashboard(request):
    events = Event.objects.order_by("starts_at")

    return render(
        request,
        "checkin/dashboard.html",
        {"events": events},
    )


@never_cache
@staff_required
@require_http_methods(["GET", "POST"])
def event_checkin(request, event_id):
    event = get_object_or_404(
        Event,
        pk=event_id,
    )

    event_date = timezone.localtime(
        event.starts_at
    ).date()

    can_check_in = (
        timezone.localdate() == event_date
    )

    form = TicketCheckInForm(
        request.POST if request.method == "POST" else None
    )

    result = None

    if request.method == "POST" and form.is_valid():
        result = check_in_ticket(
            event=event,
            ticket_code=form.cleaned_data["ticket_code"],
            staff_user=request.user,
        )

    return render(
        request,
        "checkin/event_checkin.html",
        {
            "event": event,
            "form": form,
            "result": result,
            "can_check_in": can_check_in,
        },
    )


@never_cache
@staff_required
@require_GET
def event_attendees(request, event_id):
    event = get_object_or_404(
        Event,
        pk=event_id,
    )

    registrations = Registration.objects.filter(
        event=event
    )

    # Calculate statistics before applying search filters.
    stats = registrations.aggregate(
        registered_count=Count(
            "id",
            filter=Q(
                status__in=[
                    Registration.Status.CONFIRMED,
                    Registration.Status.CHECKED_IN,
                ]
            ),
        ),
        checked_in_count=Count(
            "id",
            filter=Q(
                status=Registration.Status.CHECKED_IN
            ),
        ),
    )

    registered_count = stats["registered_count"]
    checked_in_count = stats["checked_in_count"]

    spots_left = max(
        event.capacity - registered_count,
        0,
    )

    # Search is restricted to this event's registrations.
    search_query = request.GET.get(
        "q", ""
    ).strip()[:100]

    if search_query:
        registrations = registrations.filter(
            Q(full_name__icontains=search_query)
            | Q(ticket_code__icontains=search_query)
        )

    registrations = registrations.order_by(
        "full_name",
        "pk",
    )

    paginator = Paginator(registrations, 10)

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "checkin/event_attendees.html",
        {
            "event": event,
            "page_obj": page_obj,
            "search_query": search_query,
            "registered_count": registered_count,
            "checked_in_count": checked_in_count,
            "spots_left": spots_left,
        },
    )
