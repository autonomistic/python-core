from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from .extensions import db, login_manager
from .forms import LoginForm, RegisterForm
from .models import User, UserStats, AppSetting, ActivityLog
from .utils import update_streak


auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _registration_open() -> bool:
    value = AppSetting.get_value("registration_open", None)
    if value is None and User.query.count() > 0:
        return False
    if value is None:
        return True
    return value.lower() == "true"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Welcome back.", "success")
            return redirect(url_for("main.dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if not _registration_open():
        return render_template("auth/register_closed.html"), 403
    form = RegisterForm()
    if form.validate_on_submit():
        invite = current_app.config.get("INVITE_CODE", "")
        if not invite or form.invite_code.data != invite:
            flash("Invalid invite code.", "error")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html", form=form)

        first_user = User.query.count() == 0
        user = User(email=form.email.data.lower(), is_admin=first_user)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        stats = UserStats(user_id=user.id)
        db.session.add(stats)
        db.session.add(ActivityLog(user_id=user.id, action="register", ref_type="user", ref_id=user.id))

        if first_user:
            AppSetting.set_value("registration_open", "false")

        db.session.commit()
        login_user(user)
        update_streak(user.stats, date.today())
        db.session.commit()
        flash("Account created.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("auth.login"))
