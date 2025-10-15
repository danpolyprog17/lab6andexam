from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from . import bp
from ..extensions import db
from ..models import User, Role


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("recipes.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("recipes.index"))
        flash("Невозможно аутентифицироваться с указанными логином и паролем", "danger")
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    ref = request.headers.get("Referer")
    return redirect(ref or url_for("recipes.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("recipes.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        last_name = request.form.get("last_name", "").strip()
        first_name = request.form.get("first_name", "").strip()
        middle_name = request.form.get("middle_name", "").strip()
        if not username or not password or not last_name or not first_name:
            flash("Заполните обязательные поля", "danger")
            return render_template("auth/register.html")
        if User.query.filter_by(username=username).first():
            flash("Пользователь с таким логином уже существует", "danger")
            return render_template("auth/register.html")
        role = Role.query.filter_by(name="user").first()
        if not role:
            role = Role(name="user", description="Пользователь")
            db.session.add(role)
            db.session.flush()
        user = User(
            username=username,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name or None,
            role=role,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Регистрация прошла успешно", "success")
        return redirect(url_for("recipes.index"))
    return render_template("auth/register.html")
