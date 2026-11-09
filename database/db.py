import sqlite3
from datetime import date
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            date        TEXT NOT NULL,
            description TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    conn.commit()
    conn.close()


def create_user(name, email, password):
    hashed = generate_password_hash(password)
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name.strip(), email.strip().lower(), hashed),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        return row
    finally:
        conn.close()

def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count > 0:
        conn.commit()
        conn.close()
        return

    user_id = cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    ).lastrowid

    today = date.today()
    expenses = [
        (user_id, 250.00, "Food", f"{today.year}-{today.month:02d}-01", "Lunch with colleagues"),
        (user_id, 80.00, "Transport", f"{today.year}-{today.month:02d}-02", "Bus fare"),
        (user_id, 1200.00, "Bills", f"{today.year}-{today.month:02d}-03", "Electricity bill"),
        (user_id, 600.00, "Health", f"{today.year}-{today.month:02d}-04", "Pharmacy"),
        (user_id, 450.00, "Entertainment", f"{today.year}-{today.month:02d}-05", "Movie night"),
        (user_id, 1800.00, "Shopping", f"{today.year}-{today.month:02d}-06", "Clothes"),
        (user_id, 150.00, "Other", f"{today.year}-{today.month:02d}-07", "Miscellaneous"),
        (user_id, 320.00, "Food", f"{today.year}-{today.month:02d}-08", "Groceries"),
    ]
    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    import datetime as _dt
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return None
        created_at = row["created_at"]
        dt = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = _dt.datetime.strptime(created_at, fmt)
                break
            except (TypeError, ValueError):
                continue
        member_since = dt.strftime("%B %Y") if dt else created_at
        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": member_since,
        }
    finally:
        conn.close()


def get_summary_stats(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
            "FROM expenses WHERE user_id = ? "
            "AND (? IS NULL OR date >= ?) "
            "AND (? IS NULL OR date <= ?)",
            (user_id, date_from, date_from, date_to, date_to),
        ).fetchone()
        total_spent = row["total"] if row is not None else 0
        transaction_count = row["cnt"] if row is not None else 0

        top_row = conn.execute(
            "SELECT category, SUM(amount) AS total "
            "FROM expenses WHERE user_id = ? "
            "AND (? IS NULL OR date >= ?) "
            "AND (? IS NULL OR date <= ?) "
            "GROUP BY category ORDER BY total DESC, category ASC LIMIT 1",
            (user_id, date_from, date_from, date_to, date_to),
        ).fetchone()
        top_category = top_row["category"] if top_row is not None else "—"

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category,
        }
    finally:
        conn.close()

def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT date, description, category, amount "
            "FROM expenses WHERE user_id = ? "
            "AND (? IS NULL OR date >= ?) "
            "AND (? IS NULL OR date <= ?) "
            "ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, date_from, date_from, date_to, date_to, limit),
        ).fetchall()
        return [
            {
                "date": r["date"],
                "description": r["description"],
                "category": r["category"],
                "amount": r["amount"],
            }
            for r in rows
        ]
    finally:
        conn.close()

def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT category AS name, SUM(amount) AS amount "
            "FROM expenses WHERE user_id = ? "
            "AND (? IS NULL OR date >= ?) "
            "AND (? IS NULL OR date <= ?) "
            "GROUP BY category ORDER BY amount DESC, name ASC",
            (user_id, date_from, date_from, date_to, date_to),
        ).fetchall()
        items = [{"name": r["name"], "amount": r["amount"]} for r in rows]
        if not items:
            return []

        total = sum(i["amount"] for i in items)
        if total == 0:
            for i in items:
                i["pct"] = 0
            return items

        for i in items:
            exact = i["amount"] / total * 100
            i["pct"] = int(round(exact))

        leftover = 100 - sum(i["pct"] for i in items)
        if items:
            items[0]["pct"] += leftover
        return items
    finally:
        conn.close()
