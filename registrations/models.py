
import secrets

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from events.models import Event


def generate_ticket_code():
    """Generate a secure, unpredictable ticket identifier."""
    return f"EP-{secrets.token_hex(16).upper()}"


class Registration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked In"
        WAITLISTED = "waitlisted", "Waitlisted"
        CANCELLED = "cancelled", "Cancelled"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )

    full_name = models.CharField(max_length=150)
    email = models.EmailField()

    mobile = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r"^09\d{9}$",
                message="Enter a valid 11-digit Philippine mobile number.",
            )
        ],
    )

    ticket_code = models.CharField(
        max_length=40,
        unique=True,
        default=generate_ticket_code,
        editable=False,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )

    registered_at = models.DateTimeField(auto_now_add=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_checkins",
    )

    class Meta:
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "email"],
                condition=models.Q(
                    status__in=[
                        "confirmed",
                        "checked_in",
                        "waitlisted",
                    ]
                ),
                name="unique_active_email_per_event",
            )
        ]

    def __str__(self):
        return f"{self.full_name} - {self.event.title}"

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)
