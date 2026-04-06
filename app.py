from __future__ import annotations

import os
from calendar import monthrange
from datetime import date, datetime
from functools import wraps
from typing import Any

import pymysql
from flask import Flask, flash, g, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "canteen")

BASE_HTML = """
<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<style>
:root{
  --bg:#f5f7fb;
  --card:#ffffff;
  --border:#dfe6ee;
  --text:#1f2937;
  --muted:#6b7280;
  --primary:#2563eb;
  --primary-hover:#1d4ed8;
  --success-bg:#ecfdf5;
  --success-border:#bbf7d0;
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family:Arial,sans-serif;
  background:var(--bg);
  color:var(--text);
}
.wrap{
  max-width:1180px;
  margin:0 auto;
  padding:28px;
}
.topbar{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  margin-bottom:20px;
}
.topbar a{
  text-decoration:none;
  padding:10px 14px;
  border-radius:10px;
  background:var(--card);
  border:1px solid var(--border);
  color:var(--text);
}
.topbar a:hover{
  border-color:#c5d2e1;
}
.card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:14px;
  padding:20px;
  margin-bottom:20px;
  box-shadow:0 2px 10px rgba(15,23,42,.04);
}
.grid{
  display:grid;
  grid-template-columns:1fr;
  gap:20px;
}
h1,h2,h3{
  margin-top:0;
}
.muted{
  color:var(--muted);
}
form.inline{
  display:flex;
  gap:12px;
  align-items:end;
  flex-wrap:wrap;
}
label{
  display:flex;
  flex-direction:column;
  gap:6px;
  font-size:14px;
}
table{
  width:100%;
  border-collapse:collapse;
  margin-top:12px;
}
th,td{
  padding:12px 10px;
  border-bottom:1px solid #edf2f7;
  text-align:left;
  vertical-align:middle;
}
th{
  background:#f8fafc;
}
input,select{
  min-height:40px;
  padding:8px 10px;
  border:1px solid #cbd5e1;
  border-radius:8px;
  background:#fff;
}
input[type='number']{
  width:120px;
}
button{
  min-height:40px;
  padding:8px 14px;
  border:none;
  border-radius:8px;
  background:var(--primary);
  color:#fff;
  cursor:pointer;
  font-weight:700;
}
button:hover{
  background:var(--primary-hover);
}
.flash{
  background:var(--success-bg);
  border:1px solid var(--success-border);
  padding:10px 12px;
  border-radius:10px;
  margin-bottom:16px;
}
.kpi{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:14px;
}
.kpi .box{
  background:#f8fafc;
  border:1px solid #e5edf5;
  padding:16px;
  border-radius:12px;
}
.num{
  font-size:28px;
  font-weight:700;
  margin-top:6px;
}
.empty{
  color:var(--muted);
  padding:14px 0 4px;
}
.login-wrap{
  max-width:420px;
  margin:120px auto;
}
.login-wrap form{
  display:grid;
  gap:18px;
}
.login-wrap button{
  margin-top:6px;
}
.report-filters{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:20px;
}
.topbar a.brand{
  background:#F2D233;
  color:#000;
  font-weight:800;
  letter-spacing:1px;
  border:1px solid #e6c200;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
}
.topbar a.brand:hover{
  background:#ffd84a;
  border-color:#d4b400;
}
</style>
</head>
<body>
<div class="wrap">
  {% if session.get('operator_id') %}
  <div class="topbar">
    <a href="{{ url_for('index') }}" class="brand">KONSORT</a>
    <a href="{{ url_for('employees_page') }}">Працівники</a>
    <a href="{{ url_for('report_page') }}">Звіт їдальня</a>
    <a href="{{ url_for('factory_report_page') }}">Звіт завод</a>
    <a href="{{ url_for('logout') }}">Вихід</a>
  </div>
  {% endif %}

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
    <h1>Їдальня адміністрування</h1>
    <p class="muted">Web-редактор денної компенсації працівників та формування звітів по відвідуваннях їдальні і замовленнях заводу.</p>
  </div>
</div>
"""

LOGIN_HTML = """
<div class="login-wrap">
  <div class="card">
    <h1>KONSORT - їдальня</h1>
    <p class="muted">Авторизація адміністратора.</p>

    <form method="post" action="{{ url_for('login') }}">
      <label>
        Логін
        <input type="text" name="username" required autocomplete="username">
      </label>

      <label>
        Пароль
        <input type="password" name="password" required autocomplete="current-password">
      </label>

      <button type="submit">Увійти</button>
    </form>
  </div>
</div>
"""

EMPLOYEES_HTML = """
<div class="card">
  <h1>Працівники</h1>
  <p class="muted">У таблиці можна змінювати поля Активний та Компенсація.</p>

  {% if employees %}
  <table>
    <thead>
      <tr>
        <th>ПІБ</th>
        <th>Активний</th>
        <th>Компенсація</th>
        <th>Оновлено</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {% for row in employees %}
      <tr>
        <form method="post" action="{{ url_for('employee_update', employee_id=row['id']) }}">
          <td>{{ row['full_name'] }}</td>
          <td>
            <input type="checkbox" name="active" value="1" {% if row['active'] %}checked{% endif %}>
          </td>
          <td>
            <input type="number" name="fmoney" min="0" step="1" value="{{ row['fmoney'] }}" required>
          </td>
          <td>{{ row['updated_date'] or '' }}</td>
          <td><button type="submit">Зберегти</button></td>
        </form>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
    <div class="empty">Немає даних у таблиці employees.</div>
  {% endif %}
</div>
"""

REPORT_HTML = """
<div class="grid">

  <div class="report-filters">
    <div class="card">
      <h2>Звіт за день</h2>
      <form class="inline" method="get" action="{{ url_for('report_page') }}">
        <label>
          Дата
          <input type="date" name="day_date" value="{{ day_date }}">
        </label>
        <button type="submit" name="mode" value="day">Показати</button>
      </form>
    </div>

    <div class="card">
      <h2>Звіт за період</h2>
      <form class="inline" method="get" action="{{ url_for('report_page') }}">
        <label>
          Дата з
          <input type="date" name="start_date" value="{{ start_date }}">
        </label>
        <label>
          Дата по
          <input type="date" name="end_date" value="{{ end_date }}">
        </label>
        <button type="submit" name="mode" value="period">Показати</button>
      </form>
    </div>
  </div>

  <div class="card">
    {% if mode == 'day' %}
      <h2>Звіт за день</h2>
      {% if day_visits %}
        <table>
          <thead>
            <tr>
              <th>Дата і час</th>
              <th>Працівник</th>
              <th>Реєстрація</th>
              <th>Сума</th>
            </tr>
          </thead>
          <tbody>
            {% for row in day_visits %}
            <tr>
              <td>{{ row['visit_time_formatted'] }}</td>
              <td>{{ row['full_name'] }}</td>
              <td>{{ row['registration_type'] }}</td>
              <td>{{ '%.2f'|format(row['fmoney_from_employee'] or 0) }}</td>
            </tr>
            {% endfor %}
            <tr>
              <td></td>
              <td></td>
              <td><strong>Всього за день:</strong></td>
              <td><strong>{{ '%.2f'|format(day_total or 0) }}</strong></td>
            </tr>
          </tbody>
        </table>
      {% else %}
        <div class="empty">За цей день відвідувань немає.</div>
      {% endif %}
    {% else %}
      <h2>Звіт за період</h2>

      <div class="kpi">
        <div class="box">
          <div class="muted">Сума за період</div>
          <div class="num">{{ '%.2f'|format(month_total) }}</div>
        </div>
        <div class="box">
          <div class="muted">Кількість відвідувань</div>
          <div class="num">{{ visit_count }}</div>
        </div>
        <div class="box">
          <div class="muted">Активних працівників</div>
          <div class="num">{{ active_employees }}</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Сума</th>
          </tr>
        </thead>
        <tbody>
          {% for row in daily_totals %}
          <tr>
            <td>{{ row['visit_day'] }}</td>
            <td>{{ '%.2f'|format(row['day_total'] or 0) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% endif %}
  </div>
</div>
"""

FACTORY_REPORT_HTML = """
<div class="grid">

  <div class="report-filters">
    <div class="card">
      <h2>Звіт за день</h2>
      <form class="inline" method="get" action="{{ url_for('factory_report_page') }}">
        <label>
          Дата
          <input type="date" name="day_date" value="{{ day_date }}">
        </label>
        <button type="submit" name="mode" value="day">Показати</button>
      </form>
    </div>

    <div class="card">
      <h2>Звіт за період</h2>
      <form class="inline" method="get" action="{{ url_for('factory_report_page') }}">
        <label>
          Дата з
          <input type="date" name="start_date" value="{{ start_date }}">
        </label>
        <label>
          Дата по
          <input type="date" name="end_date" value="{{ end_date }}">
        </label>
        <button type="submit" name="mode" value="period">Показати</button>
      </form>
    </div>
  </div>

  <div class="card">
    {% if mode == 'day' %}
      <h2>Звіт завод за день</h2>
      {% if day_orders %}
        <table>
          <thead>
            <tr>
              <th>Працівник</th>
              <th>Замовлення</th>
              <th>Дата і час замовлення</th>
            </tr>
          </thead>
          <tbody>
            {% for row in day_orders %}
            <tr>
              <td>{{ row['name'] }}</td>
              <td>{{ row['bludo'] }}</td>
              <td>{{ row['data'] }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      {% else %}
        <div class="empty">За цей день замовлень немає.</div>
      {% endif %}
    {% else %}
      <h2>Звіт завод за період</h2>

      <div class="kpi">
        <div class="box">
          <div class="muted">Кількість замовлень</div>
          <div class="num">{{ order_count }}</div>
        </div>
        <div class="box">
          <div class="muted">Днів із замовленнями</div>
          <div class="num">{{ days_with_orders }}</div>
        </div>
        <div class="box">
          <div class="muted">Унікальних працівників</div>
          <div class="num">{{ unique_people }}</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Кількість замовлень</th>
          </tr>
        </thead>
        <tbody>
          {% for row in daily_orders %}
          <tr>
            <td>{{ row['order_day'] }}</td>
            <td>{{ row['order_count'] }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% endif %}
  </div>
</div>
"""

EMPLOYEE_VISITS_HTML = """
<div class="grid">
  <div class="card">
    <h1>{{ employee['full_name'] }}</h1>
    <form class="inline" method="get" action="{{ url_for('employee_visits_page', employee_id=employee['id']) }}">
      <label>
        Дата з
        <input type="date" name="start_date" value="{{ start_date }}">
      </label>

      <label>
        Дата по
        <input type="date" name="end_date" value="{{ end_date }}">
      </label>

      <button type="submit">Показати</button>
    </form>
  </div>

  <div class="card">
    <div class="kpi">
      <div class="box">
        <div class="muted">Відвідувань за місяць</div>
        <div class="num">{{ visits|length }}</div>
      </div>
      <div class="box">
        <div class="muted">Сума за місяць</div>
        <div class="num">{{ '%.2f'|format(total_sum) }}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Список дат відвідувань їдальні</h2>
    {% if visits %}
    <table>
      <thead>
        <tr>
          <th>Дата і час</th>
        </tr>
      </thead>
      <tbody>
        {% for row in visits %}
        <tr>
          <td>{{ row['visit_time_formatted'] }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
      <div class="empty">У вибраному місяці відвідувань немає.</div>
    {% endif %}
  </div>
</div>
"""


def default_period() -> tuple[str, str]:
    today = date.today()
    start = today.replace(day=1)
    end = today
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def get_db() -> pymysql.connections.Connection:
    if "db" not in g:
        g.db = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    return g.db


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "operator_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.teardown_appcontext
def close_db(_error: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def month_bounds(month_value: str) -> tuple[str, str]:
    dt = datetime.strptime(month_value, "%Y-%m")
    last_day = monthrange(dt.year, dt.month)[1]
    start = f"{dt.year}-{dt.month:02d}-01"
    end = f"{dt.year}-{dt.month:02d}-{last_day:02d}"
    return start, end


@app.route("/")
@login_required
def index():
    return render_template_string(BASE_HTML, title="Головна", content=render_template_string(INDEX_HTML))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("operator_id"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

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
            session["operator_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))

        flash("Невірний логін або пароль")

    return render_template_string(BASE_HTML, title="Вхід", content=render_template_string(LOGIN_HTML))


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")


@app.route("/employees")
@login_required
def employees_page():
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
        employees = cur.fetchall()

    html = render_template_string(EMPLOYEES_HTML, employees=employees)
    return render_template_string(BASE_HTML, title="Працівники", content=html)


@app.post("/employees/<int:employee_id>/update")
@login_required
def employee_update(employee_id: int):
    fmoney = request.form.get("fmoney", type=int)
    active = 1 if request.form.get("active") else 0

    if fmoney is None or fmoney < 0:
        flash("fmoney має бути невід’ємним числом")
        return redirect(url_for("employees_page"))

    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE employees SET fmoney = %s, active = %s WHERE id = %s",
            (fmoney, active, employee_id),
        )
    db.commit()

    flash("Збережено")
    return redirect(url_for("employees_page"))


@app.route("/report")
@login_required
def report_page():
    mode = request.args.get("mode", "day")

    day_date = request.args.get("day_date") or datetime.now().strftime("%Y-%m-%d")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = default_period()

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
        day_visits = cur.fetchall()
        day_total = sum((row["fmoney_from_employee"] or 0) for row in day_visits)

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
        daily_totals = cur.fetchall()

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
        totals = cur.fetchone()

    html = render_template_string(
        REPORT_HTML,
        mode=mode,
        day_date=day_date,
        start_date=start_date,
        end_date=end_date,
        day_visits=day_visits,
        day_total=day_total,
        daily_totals=daily_totals,
        month_total=totals["month_total"],
        visit_count=totals["visit_count"],
        active_employees=totals["active_employees"],
    )
    return render_template_string(BASE_HTML, title="Звіт їдальня", content=html)


@app.route("/report-factory")
@login_required
def factory_report_page():
    mode = request.args.get("mode", "day")

    day_date = request.args.get("day_date") or datetime.now().strftime("%Y-%m-%d")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = default_period()

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
        day_orders = cur.fetchall()

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
        daily_orders = cur.fetchall()

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
        totals = cur.fetchone()

    html = render_template_string(
        FACTORY_REPORT_HTML,
        mode=mode,
        day_date=day_date,
        start_date=start_date,
        end_date=end_date,
        day_orders=day_orders,
        daily_orders=daily_orders,
        order_count=totals["order_count"],
        days_with_orders=totals["days_with_orders"],
        unique_people=totals["unique_people"],
    )
    return render_template_string(BASE_HTML, title="Звіт завод", content=html)


@app.route("/employees/<int:employee_id>/visits")
@login_required
def employee_visits_page(employee_id: int):
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = default_period()

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, full_name, fmoney FROM employees WHERE id = %s", (employee_id,))
        employee = cur.fetchone()

        if not employee:
            flash("Працівника не знайдено")
            return redirect(url_for("employees_page"))

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
        visits = cur.fetchall()

    total_sum = len(visits) * employee["fmoney"]

    html = render_template_string(
        EMPLOYEE_VISITS_HTML,
        employee=employee,
        start_date=start_date,
        end_date=end_date,
        visits=visits,
        total_sum=total_sum,
    )
    return render_template_string(BASE_HTML, title="Відвідування", content=html)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
