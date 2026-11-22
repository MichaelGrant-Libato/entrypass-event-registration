
from django.urls import path

from . import views

app_name = "registrations"

urlpatterns = [
    path(
        "events/<int:event_id>/register/",
        views.event_registration,
        name="register",
    ),
    path(
        "confirmation/",
        views.registration_confirmation,
        name="confirmation",
    ),
]
