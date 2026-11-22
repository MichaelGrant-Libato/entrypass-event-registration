
from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "venue",
        "starts_at",
        "capacity",
        "status",
    )

    list_filter = ("status",)

    search_fields = (
        "title",
        "venue",
    )

    ordering = ("starts_at",)
