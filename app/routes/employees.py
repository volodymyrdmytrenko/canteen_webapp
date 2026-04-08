from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.decorators import login_required
from app.services.employee_service import (
    get_all_employees,
    get_employee_by_id,
    get_employee_visits,
    update_employee,
)
from app.utils.date_utils import default_period

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("/employees")
@login_required
def employees_page():
    employees = get_all_employees()
    return render_template("employees.html", title="Працівники", employees=employees, active_page="employees")


@employees_bp.post("/employees/<int:employee_id>/update")
@login_required
def employee_update_page(employee_id: int):
    fmoney = request.form.get("fmoney", type=int)
    active = 1 if request.form.get("active") else 0

    if fmoney is None or fmoney < 0:
        flash("fmoney має бути невід’ємним числом")
        return redirect(url_for("employees.employees_page"))

    update_employee(employee_id, fmoney, active)
    flash("Збережено")
    return redirect(url_for("employees.employees_page"))


@employees_bp.route("/employees/<int:employee_id>/visits")
@login_required
def employee_visits_page(employee_id: int):
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = default_period()

    employee = get_employee_by_id(employee_id)
    if not employee:
        flash("Працівника не знайдено")
        return redirect(url_for("employees.employees_page"))

    visits = get_employee_visits(employee_id, start_date, end_date)
    total_sum = len(visits) * employee["fmoney"]

    return render_template(
        "employee_visits.html",
        title="Відвідування",
        employee=employee,
        start_date=start_date,
        end_date=end_date,
        visits=visits,
        total_sum=total_sum,
        active_page="employees",
    )
