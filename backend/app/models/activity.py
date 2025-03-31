from app.extensions import db
from datetime import datetime, timezone

class Activity(db.Model):
    __tablename__ = 'activities'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)  # Nullable for default activities
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Mind + Body, Growth + Creation, Purpose + People
    description = db.Column(db.Text)
    type = db.Column(db.String(50))  # physical, mental, wellness, etc.
    xp_value = db.Column(db.Float, nullable=False, default=10.0)
    is_active = db.Column(db.Boolean, default=True)
    is_custom = db.Column(db.Boolean, default=False)  # True for user-created activities
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Define the relationship with explicit primaryjoin
    user_activities = db.relationship(
        'UserActivity',
        primaryjoin="and_(Activity.id == UserActivity.activity_id, UserActivity.is_active == True)",
        backref=db.backref('activity_ref', lazy=True),
        lazy=True
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'type': self.type,
            'is_custom': self.is_custom,
            'user_id': self.user_id
        }

class UserActivity(db.Model):
    __tablename__ = 'user_activities'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'activity_id', name='unique_user_activity'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    activity_id = db.Column(db.String(36), db.ForeignKey('activities.id'), nullable=False)  # Changed to match Activity.id
    activity_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50))
    completed = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class UserActivityLog(db.Model):
    __tablename__ = 'user_activity_logs'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    activity_id = db.Column(db.String(36), db.ForeignKey('activities.id'), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    xp_earned = db.Column(db.Float, nullable=False)
    multiplier = db.Column(db.Float, default=1.0)