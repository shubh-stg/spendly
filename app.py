import os
import re
from sqlite3 import IntegrityError

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash

from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

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

    user = {
        "name": "Alex Kumar",
        "email": "alex@example.com",
        "initials": "AK",
        "member_since": "January 2024",
    }
    stats = {
        "total_spent": "12,480",
        "transaction_count": 24,
        "top_category": "Food",
    }
    transactions = [
        {"date": "2024-05-12", "description": "Groceries — Big Bazaar", "category": "Food", "amount": "1,240"},
        {"date": "2024-05-10", "description": "Monthly electricity bill", "category": "Bills", "amount": "2,100"},
        {"date": "2024-05-08", "description": "Uber ride to office", "category": "Transport", "amount": "320"},
        {"date": "2024-05-05", "description": "Movie tickets", "category": "Entertainment", "amount": "600"},
    ]
    categories = [
        {"name": "Food", "amount": "3,840", "percent": 46},
        {"name": "Bills", "amount": "2,100", "percent": 25},
        {"name": "Transport", "amount": "1,280", "percent": 15},
        {"name": "Entertainment", "amount": "1,120", "percent": 14},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
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
