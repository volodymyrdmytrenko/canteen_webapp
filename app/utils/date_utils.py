from __future__ import annotations

from datetime import date, datetime


def default_period() -> tuple[str, str]:
    today = date.today()
    start = today.replace(day=1)
    end = today
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def today_string() -> str:
    return datetime.now().strftime("%Y-%m-%d")
