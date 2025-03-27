from app.extensions import db
from datetime import datetime, timezone

class DailyCheckIn(db.Model):
    __tablename__ = 'daily_check_ins'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.now(timezone.utc).date)
    completed = db.Column(db.Boolean, default=True)

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    xp_reward = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(255))  # JSON string for conditions

class WeeklyMission(db.Model):
    __tablename__ = 'weekly_missions'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    xp_reward = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)