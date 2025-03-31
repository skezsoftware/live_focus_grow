from app.extensions import db
from datetime import datetime, timezone, date
from app.models.activity import UserActivity

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
    last_check_in = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship with activities
    activities = db.relationship('UserActivity', backref='user', lazy=True)

    @property
    def xp_to_next_level(self):
        """Calculate XP needed for next level."""
        return self.calculate_xp_required(self.level + 1) - self.calculate_xp_required(self.level)

    @staticmethod
    def calculate_xp_required(level):
        """Calculate total XP required for a given level."""
        return 0.00027 * (level ** 1.6)

    def update_streak(self):
        """Update streak based on last check-in."""
        today = date.today()
        
        if not self.last_check_in:
            self.streak_days = 1
        elif (today - self.last_check_in).days > 1:
            self.streak_days = 1  # Reset streak
        else:
            self.streak_days += 1

        # Update multiplier (capped at 4x)
        self.multiplier = min(self.streak_days, 4)
        self.last_check_in = today

    def add_xp(self, base_xp):
        """Add XP and handle level ups."""
        earned_xp = base_xp * self.multiplier
        self.current_xp += earned_xp

        # Level up logic
        while self.current_xp >= self.xp_to_next_level:
            self.current_xp -= self.xp_to_next_level
            self.level += 1

        return earned_xp