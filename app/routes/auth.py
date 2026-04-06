from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.decorators import login_required
from app.services.auth_service import authenticate_operator

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("operator_id"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = authenticate_operator(username, password)
        if user:
            session["operator_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main.index"))

        flash("Невірний логін або пароль")

    return render_template("login.html", title="Вхід")


@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
