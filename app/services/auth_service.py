from __future__ import annotations

from werkzeug.security import check_password_hash

from app.db import get_db


def authenticate_operator(username: str, password: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT id, username, password_hash
            FROM operators
            WHERE username = %s AND active = 1
            """,
            (username,),
        )
        user = cur.fetchone()

    if user and check_password_hash(user["password_hash"], password):
        return user
    return None
