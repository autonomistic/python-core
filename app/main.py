from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from .extensions import db
from .models import Chapter, Problem, UserProblem, UserStats, ActivityLog
from .utils import add_xp, update_streak, add_daily_time


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    stats = current_user.stats
    today = date.today()
    today_activity = ActivityLog.query.filter(
        ActivityLog.user_id == current_user.id,
        ActivityLog.created_at >= datetime.combine(today, datetime.min.time()),
    ).order_by(ActivityLog.created_at.desc()).limit(10).all()

    chapters = Chapter.query.order_by(Chapter.position.asc()).all()
    chapter_progress = []
    for chapter in chapters:
        total = len(chapter.problems)
        solved = UserProblem.query.join(Problem).filter(
            UserProblem.user_id == current_user.id,
            Problem.chapter_id == chapter.id,
            UserProblem.status == "solved",
        ).count()
        pct = int((solved / total) * 100) if total else 0
        chapter_progress.append((chapter, solved, total, pct))

    return render_template(
        "dashboard.html",
        stats=stats,
        today_activity=today_activity,
        chapter_progress=chapter_progress,
    )


@main_bp.route("/chapters")
@login_required
def chapters():
    chapters = Chapter.query.order_by(Chapter.position.asc()).all()
    return render_template("chapters.html", chapters=chapters)


@main_bp.route("/chapters/<slug>")
@login_required
def chapter_detail(slug):
    chapter = Chapter.query.filter_by(slug=slug).first_or_404()
    problems = Problem.query.filter_by(chapter_id=chapter.id).all()
    status_map = {up.problem_id: up for up in UserProblem.query.filter_by(user_id=current_user.id).all()}
    return render_template("chapter.html", chapter=chapter, problems=problems, status_map=status_map)


@main_bp.route("/problems/<int:problem_id>")
@login_required
def problem_detail(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    user_problem = UserProblem.query.filter_by(user_id=current_user.id, problem_id=problem.id).first()
    if not user_problem:
        user_problem = UserProblem(user_id=current_user.id, problem_id=problem.id, last_opened_at=datetime.utcnow())
        db.session.add(user_problem)
        db.session.add(ActivityLog(user_id=current_user.id, action="open_problem", ref_type="problem", ref_id=problem.id))
        db.session.commit()
    return render_template("problem.html", problem=problem, user_problem=user_problem)


@main_bp.route("/problems/<int:problem_id>/save", methods=["POST"])
@login_required
def save_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    user_problem = UserProblem.query.filter_by(user_id=current_user.id, problem_id=problem.id).first()
    if not user_problem:
        user_problem = UserProblem(user_id=current_user.id, problem_id=problem.id)
        db.session.add(user_problem)
    user_problem.code = request.form.get("code", "")
    user_problem.notes = request.form.get("notes", "")
    user_problem.last_saved_at = datetime.utcnow()

    if request.form.get("mark_solved") == "true":
        user_problem.status = "solved"
        user_problem.solved_at = datetime.utcnow()
        add_xp(current_user.stats, problem.points)
        db.session.add(ActivityLog(user_id=current_user.id, action="solve_problem", ref_type="problem", ref_id=problem.id))
    else:
        if user_problem.status == "unsolved":
            user_problem.status = "attempted"
        db.session.add(ActivityLog(user_id=current_user.id, action="save_problem", ref_type="problem", ref_id=problem.id))

    update_streak(current_user.stats, date.today())
    db.session.commit()
    flash("Saved.", "success")
    return redirect(url_for("main.problem_detail", problem_id=problem.id))


@main_bp.route("/problems/<int:problem_id>/time", methods=["POST"])
@login_required
def add_time(problem_id):
    seconds = int(request.json.get("seconds", 0))
    if seconds <= 0:
        return jsonify({"ok": False}), 400
    user_problem = UserProblem.query.filter_by(user_id=current_user.id, problem_id=problem_id).first()
    if not user_problem:
        user_problem = UserProblem(user_id=current_user.id, problem_id=problem_id)
        db.session.add(user_problem)
    user_problem.time_spent_sec += seconds
    current_user.stats.total_time_sec += seconds
    add_daily_time(current_user.id, seconds, date.today())
    update_streak(current_user.stats, date.today())
    db.session.add(ActivityLog(user_id=current_user.id, action="time_log", ref_type="problem", ref_id=problem_id))
    db.session.commit()
    return jsonify({"ok": True})


@main_bp.route("/stats")
@login_required
def stats():
    stats = current_user.stats
    return render_template("stats.html", stats=stats)
