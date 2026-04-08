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
                a.name,
                a.bludo,
                a.data,
                COALESCE(sc.comp, 50) AS comp
            FROM a_zakaz AS a
            LEFT JOIN spec_comp AS sc ON sc.id = a.user_id
            WHERE STR_TO_DATE(a.on_data, '%%d.%%m.%%Y') = %s
            ORDER BY a.name ASC, STR_TO_DATE(a.data, '%%d.%%m.%%Y %%H:%%i') ASC, a.id ASC
            """,
            (day_date,),
        )
        rows = cur.fetchall()
    total_sum = sum(float(row["comp"] or 0) for row in rows)
    return rows, total_sum


def get_factory_daily_orders(start_date: str, end_date: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT
                DATE_FORMAT(t.order_date, '%%d.%%m.%%Y') AS order_day,
                COUNT(*) AS order_count,
                COALESCE(SUM(t.compensation), 0) AS day_total
            FROM (
                SELECT
                    STR_TO_DATE(a.on_data, '%%d.%%m.%%Y') AS order_date,
                    COALESCE(sc.comp, 50) AS compensation
                FROM a_zakaz AS a
                LEFT JOIN spec_comp AS sc ON sc.id = a.user_id
                WHERE STR_TO_DATE(a.on_data, '%%d.%%m.%%Y') BETWEEN %s AND %s
            ) AS t
            GROUP BY t.order_date
            ORDER BY t.order_date ASC
            """,
            (start_date, end_date),
        )
        rows = cur.fetchall()
    total_sum = sum(float(row["day_total"] or 0) for row in rows)
    return rows, total_sum


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
