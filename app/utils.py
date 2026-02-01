from datetime import date
import re
from .extensions import db
from .models import UserStats, DailyTime


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def level_from_xp(xp: int) -> int:
    # Simple quadratic progression
    level = 1
    while xp >= (level * level * 100):
        level += 1
    return level


def add_xp(stats: UserStats, amount: int):
    stats.xp += amount
    stats.level = level_from_xp(stats.xp)


def update_streak(stats: UserStats, today: date):
    if not stats.last_activity_date:
        stats.current_streak = 1
    else:
        delta = (today - stats.last_activity_date).days
        if delta == 0:
            return
        if delta == 1:
            stats.current_streak += 1
        else:
            stats.current_streak = 1
    if stats.current_streak > stats.longest_streak:
        stats.longest_streak = stats.current_streak
    stats.last_activity_date = today


def add_daily_time(user_id: int, seconds: int, today: date):
    row = DailyTime.query.filter_by(user_id=user_id, day=today).first()
    if not row:
        row = DailyTime(user_id=user_id, day=today, seconds=0)
        db.session.add(row)
    row.seconds += seconds
    return row
