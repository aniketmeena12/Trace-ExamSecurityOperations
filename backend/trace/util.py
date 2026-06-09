"""Small shared helpers."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime.

    We standardize on naive-UTC everywhere (DB storage, JWT exp, time-gate
    comparisons) so datetimes are always mutually comparable without tz mishaps.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
