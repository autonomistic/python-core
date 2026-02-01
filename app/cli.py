from flask.cli import with_appcontext
import click
from .extensions import db
from .models import Chapter, Problem, Tag
from .utils import slugify


@click.command("seed")
@with_appcontext
def seed():
    chapters = [
        "Basics",
        "Loops",
        "Functions",
        "Lists",
        "Dicts",
        "Strings",
        "Files",
        "OOP",
    ]
    for idx, title in enumerate(chapters, start=1):
        if not Chapter.query.filter_by(slug=slugify(title)).first():
            db.session.add(Chapter(title=title, slug=slugify(title), position=idx))
    db.session.commit()
    click.echo("Seeded chapters.")


def register_cli(app):
    app.cli.add_command(seed)
