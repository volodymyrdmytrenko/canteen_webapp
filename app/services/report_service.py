from __future__ import annotations

from app.db import get_db


def get_day_visits(day_date: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                DATE_FORMAT(v.visit_time, '%%d.%%m.%%Y %%H:%%i') AS visit_time_formatted,
                e.full_name,
                CASE
                    WHEN v.source = 'rfid' THEN '-'
                    WHEN v.source = 'manual' THEN 'Вручну'
                    ELSE 'Невідомо'
                END AS registration_type,
                e.fmoney AS fmoney_from_employee
            FROM visits v
            JOIN employees e ON e.id = v.employee_id
            WHERE DATE(v.visit_time) = %s
            ORDER BY v.visit_time ASC
            """,
            (day_date,),
        )
        rows = cur.fetchall()
    return rows, sum((row["fmoney_from_employee"] or 0) for row in rows)


def get_period_visit_totals(start_date: str, end_date: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                DATE(v.visit_time) AS visit_day,
                SUM(e.fmoney) AS day_total
            FROM visits v
            JOIN employees e ON e.id = v.employee_id
            WHERE DATE(v.visit_time) BETWEEN %s AND %s
            GROUP BY DATE(v.visit_time)
            ORDER BY DATE(v.visit_time)
            """,
            (start_date, end_date),
        )
        return cur.fetchall()


def get_visit_totals_summary(start_date: str, end_date: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(v.id) AS visit_count,
                COUNT(DISTINCT v.employee_id) AS active_employees,
                COALESCE(SUM(e.fmoney), 0) AS month_total
            FROM visits v
            JOIN employees e ON e.id = v.employee_id
            WHERE DATE(v.visit_time) BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        return cur.fetchone()


def get_day_factory_orders(day_date: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                name,
                bludo,
                data
            FROM a_zakaz
            WHERE STR_TO_DATE(on_data, '%%d.%%m.%%Y') = %s
            ORDER BY name ASC, STR_TO_DATE(data, '%%d.%%m.%%Y %%H:%%i') ASC, id ASC
            """,
            (day_date,),
        )
        return cur.fetchall()


def get_factory_daily_orders(start_date: str, end_date: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                DATE_FORMAT(order_date, '%%d.%%m.%%Y') AS order_day,
                COUNT(*) AS order_count
            FROM (
                SELECT STR_TO_DATE(on_data, '%%d.%%m.%%Y') AS order_date
                FROM a_zakaz
                WHERE STR_TO_DATE(on_data, '%%d.%%m.%%Y') BETWEEN %s AND %s
            ) AS t
            GROUP BY order_date
            ORDER BY order_date ASC
            """,
            (start_date, end_date),
        )
        return cur.fetchall()


def get_factory_totals_summary(start_date: str, end_date: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) AS order_count,
                COUNT(DISTINCT STR_TO_DATE(on_data, '%%d.%%m.%%Y')) AS days_with_orders,
                COUNT(DISTINCT name) AS unique_people
            FROM a_zakaz
            WHERE STR_TO_DATE(on_data, '%%d.%%m.%%Y') BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        return cur.fetchone()
