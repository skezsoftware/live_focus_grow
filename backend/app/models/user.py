from app.extensions import db
from datetime import datetime, timezone

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    level = db.Column(db.Integer, default=1)
    current_xp = db.Column(db.Float, default=0)
    streak_days = db.Column(db.Integer, default=0)
    multiplier = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))