# Spec: Registration

## Overview
Step 2 of the Spendly roadmap implements user registration. Visitors can create an account by submitting
name, email and password through the existing register form. The backend validates input, hashes the
password with Werkzeug, stores the user in SQLite, handles duplicate emails gracefully, and redirects
successful signups to the login page. It enables Step 3 (login/logout) by producing real user records.

## Depends on
Step 1 — Database setup (users table, get_db(), seed_db()).

## Routes
- `GET /register` — render registration form — public (already exists)
- `POST /register` — validate and create account; redirect on success or re-render form with error — public

## Database changes
No new tables or columns required (users table already exists with the needed schema).
database/db.py gains a helper function `create_user(name, email, password_hash)` (or
`create_user(name, email, password)` that hashes internally) performing a parameterized INSERT.
Duplicate email is handled via SQLite's UNIQUE constraint (sqlite3.IntegrityError).

## Templates
- **Create:** None
- **Modify:** `templates/register.html` — make form action use `url_for('register')`; keep error display; add success feedback if redirecting not used.

## Files to change
- `app.py` — make `/register` accept `methods=['GET', 'POST']`; add POST validation and create logic; redirect to `/login` on success.
- `database/db.py` — add user-creation helper (hashing done here or in app.py; DB layer stores hash); import nothing new (generate_password_hash already present).
- `templates/register.html` — `url_for()` for form action.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic lives in `database/db.py`, not routes
- Use `abort()` for HTTP errors where appropriate; use template `error` variable for validation failures
- Never log or expose password hashes

## Definition of done
- [ ] GET /register renders the form (existing behavior preserved)
- [ ] POST /register with valid data creates a new row in users with a hashed (non-plaintext) password and redirects to /login
- [ ] POST with missing/empty name, email, or password re-renders register.html showing an error and no row is created
- [ ] POST with password shorter than 8 characters shows an error
- [ ] POST with a duplicate email shows an error and no duplicate row is created
- [ ] Form action in register.html uses `url_for('register')`
- [ ] No plaintext password stored anywhere in the database
- [ ] App still runs on port 5001 with no new packages installed