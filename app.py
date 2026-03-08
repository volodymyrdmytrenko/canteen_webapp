from __future__ import annotations

import os
from calendar import monthrange
from datetime import datetime
from decimal import Decimal
from typing import Any

import pymysql
from flask import Flask, flash, redirect, render_template_string, request, url_for

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "canteen")
DB_USER = os.getenv("DB_USER", "canteen")
DB_PASSWORD = os.getenv("DB_PASSWORD", "canteen")

BASE_HTML = """
<!doctype html>
<html lang="uk">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>
    <style>
        :root {
            --bg: #0b1120;
            --card: #111827;
            --muted: #94a3b8;
            --text: #e5e7eb;
            --accent: #22c55e;
            --accent2: #3b82f6;
            --border: #1f2937;
            --warn: #f59e0b;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
        }
        .wrap {
            max-width: 1280px;
            margin: 0 auto;
            padding: 24px;
        }
        .topbar {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 20px;
        }
        .topbar a {
            color: white;
            background: #1e293b;
            text-decoration: none;
            padding: 10px 14px;
            border-radius: 10px;
            border: 1px solid #334155;
        }
        .topbar a:hover { background: #334155; }
        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 18px;
        }
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 8px 25px rgba(0,0,0,.25);
        }
        h1, h2, h3 { margin-top: 0; }
        .muted { color: var(--muted); }
        form.inline {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: end;
        }
        label {
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 14px;
        }
        input, select, button {
            border-radius: 10px;
            border: 1px solid #334155;
            background: #0f172a;
            color: white;
            padding: 10px 12px;
            min-height: 42px;
        }
        input[type='number'] { width: 130px; }
        input[type='text'], select { min-width: 220px; }
        button {
            cursor: pointer;
            background: var(--accent2);
            border: none;
            font-weight: 700;
        }
        button.save { background: var(--accent); }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }
        th, td {
            text-align: left;
            padding: 12px 10px;
            border-bottom: 1px solid #273449;
            vertical-align: middle;
        }
        th { color: #cbd5e1; }
        .flash {
            padding: 12px 14px;
            border-radius: 12px;
            background: #052e16;
            border: 1px solid #166534;
            margin-bottom: 14px;
        }
        .kpi {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
        }
        .box {
            background: #0f172a;
            border: 1px solid #273449;
            border-radius: 16px;
            padding: 16px;
        }
        .num {
            font-size: 28px;
            font-weight: 700;
            margin-top: 6px;
        }
        .row-link {
            color: #93c5fd;
            text-decoration: none;
        }
        .row-link:hover { text-decoration: underline; }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge-on { background: #14532d; color: #bbf7d0; }
        .badge-off { background: #7c2d12; color: #fed7aa; }
        .right { text-align: right; }
        .warn { color: #fcd34d; }
    </style>
</head>
<body>
    <div class="wrap">
        <div class="topbar">
            <a href="{{ url_for('index') }}">Головна</a>
            <a href="{{ url_for('employees_page') }}">Працівники</a>
            <a href="{{ url_for('report_page') }}">Звіт за місяць</a>
        </div>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {{ content|safe }}
    </div>
</body>
</html>
"""

INDEX_HTML = """
<div class="grid">
    <div class="card">
        <h1>Web-редактор працівників та звіти по їдальні</h1>
        <p class="muted">
            Застосунок працює з таблицями <b>employees</b> та <b>visits</b>.
            Редагуються поля <b>full_name</b> і <b>money</b> у таблиці employees.
        </p>
    </div>

    <div class="card">
        <h2>Що саме робить система</h2>
        <ul>
            <li>редагування працівників у таблиці <b>employees</b>;</li>
            <li>звіт по вибраному місяцю;</li>
            <li>загальна сума по днях за місяць;</li>
            <li>підсумок за весь місяць;</li>
            <li>окрема сума по кожному співробітнику за місяць;</li>
            <li>вибір співробітника і перегляд дат/часу його відвідувань їдальні.</li>
        </ul>
        <p class="muted warn">
            Розрахунок суми виконується як кількість відвідувань × поточне значення поля money у працівника.
            У таблиці visits окремої суми немає.
        </p>
    </div>
</div>
"""

EMPLOYEES_HTML = """
<div class="card">
    <h1>Працівники</h1>
    <p class="muted">Редагування полів <b>full_name</b> та <b>money</b> у таблиці <b>employees</b>.</p>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>RFID</th>
                <th>ПІБ</th>
                <th>Активний</th>
                <th>Money</th>
                <th>Оновлено</th>
                <th>Дії</th>
            </tr>
        </thead>
        <tbody>
            {% for row in employees %}
            <tr>
                <form method="post" action="{{ url_for('employee_update', employee_id=row['id']) }}">
                    <td>{{ row['id'] }}</td>
                    <td>{{ row['rfid'] or '—' }}</td>
                    <td><input type="text" name="full_name" value="{{ row['full_name'] or '' }}" style="width:100%"></td>
                    <td>
                        <select name="active">
                            <option value="1" {% if row['active'] %}selected{% endif %}>Так</option>
                            <option value="0" {% if not row['active'] %}selected{% endif %}>Ні</option>
                        </select>
                    </td>
                    <td><input type="number" step="1" name="money" value="{{ row['money'] if row['money'] is not none else 50 }}"></td>
                    <td>{{ row['updated_at'] or '—' }}</td>
                    <td>
                        <button class="save" type="submit">Зберегти</button>
                        <a class="row-link" href="{{ url_for('employee_visits_page', employee_id=row['id']) }}">Відвідування</a>
                    </td>
                </form>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
"""

REPORT_HTML = """
<div class="grid">
    <div class="card">
        <h1>Звіт за місяць</h1>
        <form class="inline" method="get" action="{{ url_for('report_page') }}">
            <label>
                Місяць
                <input type="month" name="month" value="{{ selected_month }}" required>
            </label>
            <button type="submit">Показати звіт</button>
        </form>
    </div>

    {% if selected_month %}
    <div class="card">
        <h2>Підсумки за {{ selected_month }}</h2>
        <div class="kpi">
            <div class="box">
                <div class="muted">Всього за місяць</div>
                <div class="num">{{ month_total }}</div>
            </div>
            <div class="box">
                <div class="muted">Кількість відвідувань</div>
                <div class="num">{{ visit_count }}</div>
            </div>
            <div class="box">
                <div class="muted">Активних співробітників з відвідуваннями</div>
                <div class="num">{{ active_employees }}</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Сума по днях</h2>
        <table>
            <thead>
                <tr>
                    <th>Дата</th>
                    <th class="right">Сума</th>
                </tr>
            </thead>
            <tbody>
                {% for row in daily_totals %}
                <tr>
                    <td>{{ row['visit_day'] }}</td>
                    <td class="right">{{ row['day_total'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>По кожному співробітнику за місяць</h2>
        <table>
            <thead>
                <tr>
                    <th>Співробітник</th>
                    <th class="right">Сума</th>
                    <th class="right">Кількість відвідувань</th>
                    <th>Детально</th>
                </tr>
            </thead>
            <tbody>
                {% for row in employee_totals %}
                <tr>
                    <td>{{ row['full_name'] }}</td>
                    <td class="right">{{ row['employee_total'] }}</td>
                    <td class="right">{{ row['visit_count'] }}</td>
                    <td><a class="row-link" href="{{ url_for('employee_visits_page', employee_id=row['employee_id'], month=selected_month) }}">Переглянути</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}
</div>
"""

EMPLOYEE_VISITS_HTML = """
<div class="grid">
    <div class="card">
        <h1>Відвідування співробітника</h1>
        <form class="inline" method="get" action="{{ url_for('employee_visits_page', employee_id=employee['id']) }}">
            <label>
                Працівник
                <input type="text" value="{{ employee['full_name'] }}" disabled>
            </label>
            <label>
                Місяць
                <input type="month" name="month" value="{{ selected_month }}">
            </label>
            <button type="submit">Фільтрувати</button>
        </form>
    </div>

    <div class="card">
        <div class="kpi">
            <div class="box">
                <div class="muted">Всього відвідувань</div>
                <div class="num">{{ visits|length }}</div>
            </div>
            <div class="box">
                <div class="muted">Сума за місяць</div>
                <div class="num">{{ total_sum }}</div>
            </div>
            <div class="box">
                <div class="muted">Ставка money</div>
                <div class="num">{{ employee['money'] }}</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Список дат відвідувань їдальні</h2>
        <table>
            <thead>
                <tr>
                    <th>Дата/час</th>
                    <th>Джерело</th>
                    <th class="right">Розрахункова сума</th>
                </tr>
            </thead>
            <tbody>
                {% for row in visits %}
                <tr>
                    <td>{{ row['visit_time'] }}</td>
                    <td>{{ row['source'] or '—' }}</td>
                    <td class="right">{{ row['amount'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
"""


def get_conn():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def month_bounds(month_value: str) -> tuple[str, str]:
    dt = datetime.strptime(month_value, "%Y-%m")
    last_day = monthrange(dt.year, dt.month)[1]
    start = f"{dt.year:04d}-{dt.month:02d}-01"
    end = f"{dt.year:04d}-{dt.month:02d}-{last_day:02d}"
    return start, end


def fmt_money(value: Any) -> str:
    dec = Decimal(str(value or 0))
    return f"{dec:.2f}"


@app.route("/")
def index():
    return render_template_string(BASE_HTML, title="Головна", content=render_template_string(INDEX_HTML))


@app.route("/employees")
def employees_page():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, rfid, full_name, active, updated_at, money
                FROM employees
                ORDER BY full_name ASC
                """
            )
            employees = cur.fetchall()
    html = render_template_string(EMPLOYEES_HTML, employees=employees)
    return render_template_string(BASE_HTML, title="Працівники", content=html)


@app.post("/employees/<int:employee_id>/update")
def employee_update(employee_id: int):
    full_name = (request.form.get("full_name") or "").strip()
    active = 1 if request.form.get("active") == "1" else 0
    try:
        money = int(request.form.get("money") or 50)
    except ValueError:
        money = 50

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE employees
                SET full_name = %s,
                    active = %s,
                    money = %s
                WHERE id = %s
                """,
                (full_name, active, money, employee_id),
            )
    flash("Дані працівника збережено")
    return redirect(url_for("employees_page"))


@app.route("/report")
def report_page():
    selected_month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    start_date, end_date = month_bounds(selected_month)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DATE(v.visit_time) AS visit_day,
                       CAST(SUM(e.money) AS DECIMAL(10,2)) AS day_total
                FROM visits v
                JOIN employees e ON e.id = v.employee_id
                WHERE DATE(v.visit_time) BETWEEN %s AND %s
                GROUP BY DATE(v.visit_time)
                ORDER BY DATE(v.visit_time)
                """,
                (start_date, end_date),
            )
            daily_totals = cur.fetchall()

            cur.execute(
                """
                SELECT e.id AS employee_id,
                       e.full_name,
                       COUNT(v.id) AS visit_count,
                       CAST(COUNT(v.id) * e.money AS DECIMAL(10,2)) AS employee_total
                FROM visits v
                JOIN employees e ON e.id = v.employee_id
                WHERE DATE(v.visit_time) BETWEEN %s AND %s
                GROUP BY e.id, e.full_name, e.money
                ORDER BY e.full_name ASC
                """,
                (start_date, end_date),
            )
            employee_totals = cur.fetchall()

            cur.execute(
                """
                SELECT COUNT(v.id) AS visit_count,
                       COUNT(DISTINCT v.employee_id) AS active_employees,
                       CAST(COALESCE(SUM(e.money), 0) AS DECIMAL(10,2)) AS month_total
                FROM visits v
                JOIN employees e ON e.id = v.employee_id
                WHERE DATE(v.visit_time) BETWEEN %s AND %s
                """,
                (start_date, end_date),
            )
            totals_row = cur.fetchone()

    for row in daily_totals:
        row["day_total"] = fmt_money(row["day_total"])
    for row in employee_totals:
        row["employee_total"] = fmt_money(row["employee_total"])

    html = render_template_string(
        REPORT_HTML,
        selected_month=selected_month,
        daily_totals=daily_totals,
        employee_totals=employee_totals,
        month_total=fmt_money(totals_row["month_total"]),
        visit_count=totals_row["visit_count"] or 0,
        active_employees=totals_row["active_employees"] or 0,
    )
    return render_template_string(BASE_HTML, title="Звіт", content=html)


@app.route("/employees/<int:employee_id>/visits")
def employee_visits_page(employee_id: int):
    selected_month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    start_date, end_date = month_bounds(selected_month)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name, money, active
                FROM employees
                WHERE id = %s
                """,
                (employee_id,),
            )
            employee = cur.fetchone()

            if not employee:
                flash("Працівника не знайдено")
                return redirect(url_for("employees_page"))

            cur.execute(
                """
                SELECT v.id,
                       v.visit_time,
                       v.source,
                       CAST(e.money AS DECIMAL(10,2)) AS amount
                FROM visits v
                JOIN employees e ON e.id = v.employee_id
                WHERE v.employee_id = %s
                  AND DATE(v.visit_time) BETWEEN %s AND %s
                ORDER BY v.visit_time DESC
                """,
                (employee_id, start_date, end_date),
            )
            visits = cur.fetchall()

    total_sum = sum(Decimal(str(v["amount"] or 0)) for v in visits)
    for row in visits:
        row["amount"] = fmt_money(row["amount"])

    html = render_template_string(
        EMPLOYEE_VISITS_HTML,
        employee=employee,
        selected_month=selected_month,
        visits=visits,
        total_sum=fmt_money(total_sum),
    )
    return render_template_string(BASE_HTML, title="Відвідування", content=html)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
