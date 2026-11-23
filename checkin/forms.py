
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


class StaffLoginForm(AuthenticationForm):
    """Allow only active staff accounts to sign in."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        if not user.is_staff:
            raise ValidationError(
                "Invalid username or password.",
                code="invalid_login",
            )
