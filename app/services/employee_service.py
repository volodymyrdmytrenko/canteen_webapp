from __future__ import annotations

from app.db import get_db


def get_all_employees():
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                full_name,
                active,
                fmoney,
                DATE_FORMAT(updated_at, '%d.%m.%Y') AS updated_date
            FROM employees
            ORDER BY full_name
            """
        )
        return cur.fetchall()


def update_employee(employee_id: int, fmoney: int, active: int) -> None:
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE employees SET fmoney = %s, active = %s WHERE id = %s",
            (fmoney, active, employee_id),
        )
    db.commit()


def get_employee_by_id(employee_id: int):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, full_name, fmoney FROM employees WHERE id = %s", (employee_id,))
        return cur.fetchone()


def get_employee_visits(employee_id: int, start_date: str, end_date: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                visit_time,
                DATE_FORMAT(visit_time, '%%d.%%m.%%Y %%H:%%i') AS visit_time_formatted
            FROM visits
            WHERE employee_id = %s
              AND DATE(visit_time) BETWEEN %s AND %s
            ORDER BY visit_time ASC
            """,
            (employee_id, start_date, end_date),
        )
        return cur.fetchall()
