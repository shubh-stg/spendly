"""Compatibility module: query helpers live in `database.db`.

Spec step 5 references `database.queries`; re-export them here so both
import paths work (`database.db` is the canonical location)."""

from database.db import (  # noqa: F401
    get_db,
    get_user_by_email,
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)
