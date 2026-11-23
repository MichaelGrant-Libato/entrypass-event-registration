# EntryPass

Event registration and attendance management built with Django.

**Live application:** https://entrypass.onrender.com

EntryPass implements the core (Level 1) assessment scope for event registration and attendance. Attendees can view published events, reserve an available seat, and receive a QR ticket. Authorized staff can verify ticket codes on the event day and monitor attendance from a dedicated workspace.

## Features

### Attendee experience
- Browse upcoming published events with dates, venues, and remaining capacity.
- Register using a full name, email address, and an 11-digit Philippine mobile number (`09XXXXXXXXX`).
- Prevent duplicate active registrations under the same email address for an event.
- Stop accepting registrations once an event reaches capacity or begins.
- Generate a unique, unpredictable ticket code and its corresponding QR image.
- Retrieve an existing ticket using the ticket code and registration email.

### Staff workspace
- Authenticate with a staff-enabled Django account.
- View events and manage attendance for a selected event.
- Validate ticket codes and record check-ins on the scheduled event date (Asia/Manila).
- Reject invalid tickets and prevent repeat check-ins.
- View attendee records, registration and check-in counts, remaining capacity, and check-in timestamps.
- Search attendees by name or ticket code, with paginated results.

## Technology

| Layer | Implementation |
| --- | --- |
| Application | Python 3.14.5, Django 5.2.19 |
| Interface | Django templates, HTML, CSS |
| Database | PostgreSQL (deployment), SQLite (local development) |
| QR tickets | `qrcode`, Pillow |
| Production serving | Gunicorn, WhiteNoise |
| Hosting | Render |

## Running locally

The commands below use Windows Command Prompt. Python 3.14 and Git are required.

1. Clone the repository and create a virtual environment:

   ```cmd
   git clone https://github.com/MichaelGrant-Libato/entrypass-event-registration.git
   cd entrypass-event-registration
   py -3.14 -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   ```

2. Create your local environment file:

   ```cmd
   copy .env.example .env
   ```

   Edit `.env` and provide a unique `DJANGO_SECRET_KEY`. Keep `DJANGO_DEBUG=True` and leave `DATABASE_URL` empty to use SQLite locally. Generate a secret key with:

   ```cmd
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   For a demo staff account, set `DEMO_STAFF_PASSWORD` to a unique password of at least 12 characters. The default username is `entrypass_demo`. Do not commit `.env`.

3. Initialize the database and optional demo data:

   ```cmd
   python manage.py migrate
   python manage.py seed_demo
   ```

4. Start the development server:

   ```cmd
   python manage.py runserver
   ```

   Open http://127.0.0.1:8000/.

**Note:** An existing `DATABASE_URL` in your system environment takes precedence over the value in `.env`. To clear it for the current Windows CMD session, run `set DATABASE_URL=`.

## Demo data and staff access

`python manage.py seed_demo` creates:
- **Cebu Dev Meetup 2026** — a published event scheduled for December 6, 2026, with 30 seats.
- **EntryPass Demo - Fully Booked** — a published event scheduled for December 8, 2026, with all three seats occupied.
- **EntryPass Door Demo** — a date-specific event for demonstrating ticket verification and check-in.

The command can be run again without duplicating the same seeded registrations. If `DEMO_STAFF_PASSWORD` is provided, it also creates a staff account when that username does not already exist.

**Demo staff username:** `entrypass_demo`  
**Password:** Provided separately to the evaluator; not stored in this repository.

The two fixed-date examples are intended for the November–December 2026 assessment. For later demonstrations, update their dates or create new upcoming events in Django admin.

## Testing

Run the project checks and automated test suite:

```cmd
python manage.py check
python manage.py test events registrations checkin
```

The current suite contains **58 tests**, covering the event, registration, ticket, staff authentication, check-in, attendee management, and demo-seeding workflows.

## Deployment

The live application runs on Render with PostgreSQL. Configuration is supplied through environment variables rather than committed secrets.

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django signing key |
| `DJANGO_DEBUG` | Set to `False` in production |
| `DATABASE_URL` | PostgreSQL connection URL |
| `DEMO_STAFF_USERNAME` | Demo staff username |
| `DEMO_STAFF_PASSWORD` | Demo staff password |
| `DJANGO_ALLOWED_HOSTS` | Optional additional allowed hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Optional additional trusted HTTPS origins |

**Build command:**

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start command used for the assessment deployment:**

```bash
python manage.py migrate --noinput && python manage.py seed_demo && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000}
```

The seed command executes on service startup in this demo configuration. The free Render database is temporary and should not be treated as durable production storage.

## Known limitations

- The QR image encodes the ticket code; staff currently enter that code manually. Camera-based QR scanning is not implemented.
- Tickets are displayed in the browser; the app does not send tickets by email or SMS.
- Ticket lookup requires both the code and the email used at registration.
- Event administration is available through Django admin, not a separate public-facing event management interface.
- The demonstration uses date-specific seed data and a free-tier hosting environment. Availability and seeded event dates may require maintenance after the assessment period.

## Repository

Source code: https://github.com/MichaelGrant-Libato/entrypass-event-registration
