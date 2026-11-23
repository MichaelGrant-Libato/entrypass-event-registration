
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.views.decorators.cache import never_cache

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
