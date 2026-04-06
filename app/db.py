from __future__ import annotations

from typing import Any

import pymysql
from flask import current_app, g


def get_db() -> pymysql.connections.Connection:
    if "db" not in g:
        g.db = pymysql.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    return g.db


def close_db(_error: Any = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()
