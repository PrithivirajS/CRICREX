# CRICREX — responsive cricket match booking MVP

A locally runnable Flask prototype with responsive dark-navy/green UI, role-based registration, team creation, ground listing/search, match publishing, opponent requests, umpire/scorer profiles and service booking requests.

## Run locally

Requirements: Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. SQLite database `cricrex.db` is created automatically. The app seeds sample grounds on first run. Delete `cricrex.db` to reset the local demo data.

Demo ground-owner login: `grounds@cricrex.demo` / `Demo@123`.

## Current MVP scope

- Account registration and login with hashed passwords and roles: captain, ground owner, umpire, scorer.
- Create teams and add a comma-separated player roster.
- Ground discovery by name/location and ground owner listings.
- Create match posts with date/time, format, fee, optional ground, opponent/official needs.
- Browse open matches and send opponent requests; creator can accept/reject.
- Umpire/scorer directory, profile creation and booking requests.
- Provider dashboard can accept/reject service booking requests and record a payment status (no money is collected).
- Role-specific dashboard summaries.

## Important prototype limitations

This is an MVP starter, not production-ready. The service booking flow should be enhanced to let captains select their matches in the booking form and notify providers; current official listing UI intentionally shows booking as disabled until the match-selection workflow is completed. Ground booking calendar, ground-slot conflict prevention, payment gateway, email/SMS notifications, admin moderation, file uploads, location maps, audit trails and formal cancellation/refund rules are not implemented yet. Opponent-request duplicate prevention and full concurrency controls should be added before launch. Add CSRF protection, rate limiting, email verification, password reset, stronger session settings, audit logs and automated tests before production.

## Suggested production architecture

- Frontend: HTML/CSS/JavaScript for MVP; React/Next.js can be introduced if richer client-side flows are needed.
- Backend: Flask REST API + SQLAlchemy/Alembic, role-based access and validation.
- Database: MySQL 8 or managed PostgreSQL; SQLite is only for local demo.
- Hosting: AWS Lightsail/EC2 or a managed app platform; managed DB, object storage for photos, domain + TLS, automated backups and monitoring.
- Payments: Razorpay/PayU integration after booking and cancellation rules are finalized. Never store card details.

## Configuration

- Set `SECRET_KEY` to a long random value before deployment.
- Set `CRICREX_DB` to an alternate SQLite database path for local use.
- The included database uses SQLite to make the demo easy to run. For production, migrate to MySQL/PostgreSQL with migrations rather than sharing SQLite over multiple app workers.
