# Spec: Login and Logout

## Overview
Step 3 of the Spendly roadmap adds authentication flow. Registered users can sign in with email
and password; the app verifies credentials against the hashed password stored in SQLite, starts a
Flask session, and redirects to the landing page. Logout clears the session and returns the user
to the landing page. This enables protected pages (Step 4+) and makes registration meaningful.

## Depends on
Step 1 — Database setup, Step 2 — Registration (users table, `create_user`, `/register`, login page).

## Routes
- `POST /login` — validate credentials, start session on success — public
- `GET /logout` — clear session and redirect — public (replaces Step 3 stub)

## Database changes
No schema changes. `database/db.py` gains `get_user_by_email(email)` returning the matching
`users` row (or `None`) via a parameterized `SELECT`. Password verification stays in the route
using Werkzeug's `check_password_hash` against the returned `password_hash`.

## Templates
- **Create:** None
- **Modify:** `templates/login.html` — ensure error/flash display works with POST handler (already wired).
- **Modify:** `templates/base.html` — conditionally show account/logout links when `session` has a user, register/login when anonymous.

## Files to change
- `app.py` — import `session` and `check_password_hash`, import `get_user_by_email`, add POST handling to `/login`, implement `/logout`.
- `database/db.py` — add `get_user_by_email` helper.
- `templates/login.html` — minor alignment with POST flow.
- `templates/base.html` — session-aware navigation.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords verified with werkzeug `check_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Never expose or log passwords
- Session state stored only under `session["user_id"]` (and optional cached name)
- Do not implement `/profile` or expense routes (still stubs for later steps)

## Definition of done
- [ ] POST /login with valid credentials sets `session["user_id"]` and redirects to `/` (302)
- [ ] POST /login with unknown email or wrong password re-renders `login.html` with an error and no session is set
- [ ] POST /login with missing fields re-renders with an error
- [ ] GET /logout clears the session and redirects to `/`
- [ ] After logout, subsequent request has no `session["user_id"]`
- [ ] Base navigation shows session-aware links
- [ ] `database/db.py` retains parameterized queries only
- [ ] App runs on port 5001 with no new packages