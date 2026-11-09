import os
import re
from datetime import date, datetime, timedelta
from sqlite3 import IntegrityError

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash

def _valid_iso_date(value):
    if not value:
        return None
    value = value.strip()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    return value



from database.db import (
    get_db,
    init_db,
    seed_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        error = None
        if not name or not email or not password:
            error = "Name, email, and password are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            error = "Please enter a valid email address."

        if error:
            return render_template("register.html", error=error, name=name, email=email)

        try:
            create_user(name, email, password)
        except IntegrityError:
            return render_template(
                "register.html",
                error="An account with that email already exists.",
                name=name,
                email=email,
            )

        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return render_template("login.html", error="Email and password are required.", email=email)

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.", email=email)

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        flash("Please log in to view your profile.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user_data = get_user_by_id(user_id)
    if user_data is None:
        session.clear()
        flash("Please log in to view your profile.", "error")
        return redirect(url_for("login"))

    date_from = _valid_iso_date(request.args.get("date_from"))
    date_to = _valid_iso_date(request.args.get("date_to"))
    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.", "error")
        date_from = None
        date_to = None

    name = user_data["name"]
    initials = "".join(part[0].upper() for part in name.split() if part)[:2]

    user = {
        "name": name,
        "email": user_data["email"],
        "initials": initials,
        "member_since": user_data["member_since"],
    }
    stats = get_summary_stats(user_id, date_from=date_from, date_to=date_to)
    transactions = get_recent_transactions(user_id, limit=10, date_from=date_from, date_to=date_to)
    categories = get_category_breakdown(user_id, date_from=date_from, date_to=date_to)

    today = date.today()
    this_month_from = today.replace(day=1).isoformat()
    last_3_months_from = (today - timedelta(days=90)).isoformat()
    last_6_months_from = (today - timedelta(days=180)).isoformat()
    preset_to = today.isoformat()

    active_preset = None
    if date_from == this_month_from and date_to == preset_to:
        active_preset = "this_month"
    elif date_from == last_3_months_from and date_to == preset_to:
        active_preset = "last_3_months"
    elif date_from == last_6_months_from and date_to == preset_to:
        active_preset = "last_6_months"
    elif not date_from and not date_to:
        active_preset = "all_time"

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        date_from=date_from,
        date_to=date_to,
        active_preset=active_preset,
        preset_this_month_from=this_month_from,
        preset_last_3_months_from=last_3_months_from,
        preset_last_6_months_from=last_6_months_from,
        preset_to=preset_to,
    )

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
