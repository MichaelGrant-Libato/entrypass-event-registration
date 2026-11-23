from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django import forms


class StaffLoginForm(AuthenticationForm):
    """Allow only active staff accounts to sign in."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        if not user.is_staff:
            raise ValidationError(
                "Invalid username or password.",
                code="invalid_login",
            )


class TicketCheckInForm(forms.Form):
    ticket_code = forms.CharField(
        label="Ticket code",
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "EP-XXXXXXXXXXXXXXXX...",
            "autocomplete": "off",
            "spellcheck": "false",
            "autofocus": True,
        }),
    )

    def clean_ticket_code(self):
        return self.cleaned_data[
            "ticket_code"
        ].strip().upper()

