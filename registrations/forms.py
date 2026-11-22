
from django import forms


class AttendeeRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label="Full name",
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "e.g. Ana Cruz",
            "autocomplete": "name",
        }),
    )

    email = forms.EmailField(
        label="Email address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "class": "form-input",
            "placeholder": "e.g. ana@example.com",
            "autocomplete": "email",
        }),
    )

    mobile = forms.RegexField(
        label="Mobile number",
        regex=r"^09\d{9}$",
        max_length=11,
        min_length=11,
        error_messages={
            "invalid": "Enter an 11-digit mobile number starting with 09.",
            "min_length": "Enter an 11-digit mobile number starting with 09.",
            "max_length": "Enter an 11-digit mobile number starting with 09.",
        },
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "09XXXXXXXXX",
            "autocomplete": "tel",
            "inputmode": "numeric",
            "maxlength": "11",
        }),
    )

    def clean_full_name(self):
        name = self.cleaned_data["full_name"].strip()

        if len(name) < 2:
            raise forms.ValidationError(
                "Please enter your full name."
            )

        return name

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class TicketLookupForm(forms.Form):
    ticket_code = forms.CharField(
        label="Ticket code",
        max_length=40,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "EP-XXXXXXXX...",
            "autocomplete": "off",
            "spellcheck": "false",
        }),
    )

    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={
            "class": "form-input",
            "placeholder": "Email used during registration",
            "autocomplete": "email",
        }),
    )

    def clean_ticket_code(self):
        return self.cleaned_data[
            "ticket_code"
        ].strip().upper()

    def clean_email(self):
        return self.cleaned_data[
            "email"
        ].strip().lower()

