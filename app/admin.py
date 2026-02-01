import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from .extensions import db
from .forms import ChapterForm, ProblemForm
from .models import Chapter, Problem, Tag
from .utils import slugify


admin_bp = Blueprint("admin", __name__)


def _require_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@admin_bp.route("/")
@login_required
def index():
    _require_admin()
    chapters = Chapter.query.order_by(Chapter.position.asc()).all()
    return render_template("admin/index.html", chapters=chapters)


@admin_bp.route("/chapters/new", methods=["GET", "POST"])
@login_required
def new_chapter():
    _require_admin()
    form = ChapterForm()
    if form.validate_on_submit():
        chapter = Chapter(
            title=form.title.data,
            slug=slugify(form.title.data),
            position=form.position.data or 0,
        )
        db.session.add(chapter)
        db.session.commit()
        flash("Chapter created.", "success")
        return redirect(url_for("admin.index"))
    return render_template("admin/chapters.html", form=form)


@admin_bp.route("/problems/new", methods=["GET", "POST"])
@login_required
def new_problem():
    _require_admin()
    form = ProblemForm()
    chapters = Chapter.query.order_by(Chapter.position.asc()).all()
    if form.validate_on_submit():
        chapter_id = int(request.form.get("chapter_id"))
        problem = Problem(
            chapter_id=chapter_id,
            title=form.title.data,
            difficulty=form.difficulty.data,
            points=form.points.data or 10,
            prompt=form.prompt.data,
        )
        tags = [t.strip().lower() for t in (form.tags.data or "").split(",") if t.strip()]
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            problem.tags.append(tag)
        db.session.add(problem)
        db.session.commit()
        flash("Problem created.", "success")
        return redirect(url_for("admin.index"))
    return render_template("admin/problems.html", form=form, chapters=chapters)


@admin_bp.route("/import", methods=["GET", "POST"])
@login_required
def bulk_import():
    _require_admin()
    if request.method == "POST":
        raw = request.form.get("payload", "")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            flash("Invalid JSON.", "error")
            return render_template("admin/import.html")
        created = 0
        for chapter_data in data.get("chapters", []):
            chapter = Chapter.query.filter_by(slug=slugify(chapter_data["title"])).first()
            if not chapter:
                chapter = Chapter(title=chapter_data["title"], slug=slugify(chapter_data["title"]), position=chapter_data.get("position", 0))
                db.session.add(chapter)
                db.session.flush()
            for p in chapter_data.get("problems", []):
                problem = Problem(
                    chapter_id=chapter.id,
                    title=p["title"],
                    difficulty=p.get("difficulty", "easy"),
                    points=p.get("points", 10),
                    prompt=p.get("prompt", ""),
                )
                tags = [t.strip().lower() for t in p.get("tags", []) if t.strip()]
                for tag_name in tags:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    problem.tags.append(tag)
                db.session.add(problem)
                created += 1
        db.session.commit()
        flash(f"Imported {created} problems.", "success")
        return redirect(url_for("admin.index"))
    return render_template("admin/import.html")
