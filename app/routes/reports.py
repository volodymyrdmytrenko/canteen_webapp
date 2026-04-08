from __future__ import annotations

from flask import Blueprint, render_template, request

from app.decorators import login_required
from app.services.report_service import (
    get_day_factory_orders,
    get_day_visits,
    get_factory_daily_orders,
    get_factory_totals_summary,
    get_period_visit_totals,
    get_visit_totals_summary,
)
from app.utils.date_utils import default_period, today_string

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/report")
@login_required
def report_page():
    mode = request.args.get("mode", "day")
    day_date = request.args.get("day_date") or today_string()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = default_period()

    day_visits, day_total = get_day_visits(day_date)
    daily_totals = get_period_visit_totals(start_date, end_date)
    totals = get_visit_totals_summary(start_date, end_date)

    return render_template(
        "report.html",
        title="Звіт їдальня",
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
        active_page="report",
    )


@reports_bp.route("/report-factory")
@login_required
def factory_report_page():
    mode = request.args.get("mode", "day")
    day_date = request.args.get("day_date") or today_string()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = default_period()

    day_orders, day_total = get_day_factory_orders(day_date)
    daily_orders, period_total = get_factory_daily_orders(start_date, end_date)
    totals = get_factory_totals_summary(start_date, end_date)

    return render_template(
        "factory_report.html",
        title="Звіт завод",
        mode=mode,
        day_date=day_date,
        start_date=start_date,
        end_date=end_date,
        day_orders=day_orders,
        day_total=day_total,
        daily_orders=daily_orders,
        order_count=totals["order_count"],
        days_with_orders=totals["days_with_orders"],
        unique_people=totals["unique_people"],
        period_total=period_total,
        active_page="factory",
    )
