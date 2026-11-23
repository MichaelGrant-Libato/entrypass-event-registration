
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import TicketCheckInForm
from .services import check_in_ticket

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
