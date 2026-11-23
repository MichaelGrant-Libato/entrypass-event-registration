
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import StaffLoginForm
from . import views

app_name = "checkin"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "events/<int:event_id>/checkin/",
        views.event_checkin,
        name="event_checkin",
    ),
    path(
        "login/",
        LoginView.as_view(
            template_name="checkin/login.html",
            authentication_form=StaffLoginForm,
            next_page="checkin:dashboard",
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(
            next_page="checkin:login",
        ),
        name="logout",
    ),
]
