from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    venue = models.CharField(max_length=255)

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1),
                name="event_capacity_at_least_one"
            )
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        if self.starts_at and self.ends_at:
            if self.ends_at <= self.starts_at:
                raise ValidationError({
                    "ends_at": "End time must be after start time."
                })
