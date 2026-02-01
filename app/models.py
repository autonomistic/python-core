from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db


class AppSetting(db.Model):
    __tablename__ = "app_settings"
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(256), nullable=False)

    @staticmethod
    def get_value(key, default=None):
        setting = AppSetting.query.get(key)
        if not setting:
            return default
        return setting.value

    @staticmethod
    def set_value(key, value):
        setting = AppSetting.query.get(key)
        if not setting:
            setting = AppSetting(key=key, value=str(value))
            db.session.add(setting)
        else:
            setting.value = str(value)
        db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stats = db.relationship("UserStats", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserStats(db.Model):
    __tablename__ = "user_stats"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    total_time_sec = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, nullable=True)


class Chapter(db.Model):
    __tablename__ = "chapters"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    position = db.Column(db.Integer, default=0)

    problems = db.relationship("Problem", backref="chapter", cascade="all, delete-orphan")


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)


class ProblemTag(db.Model):
    __tablename__ = "problem_tags"
    problem_id = db.Column(db.Integer, db.ForeignKey("problems.id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), primary_key=True)


class Problem(db.Model):
    __tablename__ = "problems"
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapters.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(32), nullable=False)
    points = db.Column(db.Integer, default=10)
    prompt = db.Column(db.Text, default="")

    tags = db.relationship("Tag", secondary="problem_tags", backref="problems")


class UserProblem(db.Model):
    __tablename__ = "user_problems"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey("problems.id"), nullable=False)
    status = db.Column(db.String(20), default="unsolved")
    code = db.Column(db.Text, default="")
    notes = db.Column(db.Text, default="")
    attempts = db.Column(db.Integer, default=0)
    time_spent_sec = db.Column(db.Integer, default=0)
    last_opened_at = db.Column(db.DateTime, nullable=True)
    last_saved_at = db.Column(db.DateTime, nullable=True)
    solved_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref="user_problems")
    problem = db.relationship("Problem", backref="user_problems")


class ActivityLog(db.Model):
    __tablename__ = "activity_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    ref_type = db.Column(db.String(32), nullable=True)
    ref_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    meta_json = db.Column(db.Text, default="{}")


class DailyTime(db.Model):
    __tablename__ = "daily_time"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    day = db.Column(db.Date, default=date.today, nullable=False)
    seconds = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint("user_id", "day", name="uq_daily_time"),)
