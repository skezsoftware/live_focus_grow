"""update activities schema

Revision ID: update_activities_schema
Revises: a9ccfd8c614b
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers, used by Alembic
revision = 'update_activities_schema'
down_revision = 'a9ccfd8c614b'
branch_labels = None
depends_on = None

def upgrade():
    # Get database connection
    connection = op.get_bind()
    
    # Start fresh - drop existing tables if they exist
    try:
        connection.execute(sa.text("DROP TABLE IF EXISTS user_activities CASCADE"))
        print("Dropped user_activities table")
    except Exception as e:
        print(f"Error dropping user_activities: {e}")
        
    # Create user_activities table
    op.create_table('user_activities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('activity_id', sa.String(36), sa.ForeignKey('activities.id'), nullable=False),
        sa.Column('completed', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow)
    )
    
    # Add unique constraint
    op.create_unique_constraint('unique_user_activity', 'user_activities', ['user_id', 'activity_id'])
    
    # Insert default activities
    default_activities = [
        ('Morning Meditation', 'Mind + Body', 'Start your day with a 10-minute meditation session'),
        ('Daily Exercise', 'Mind + Body', 'Complete 30 minutes of physical activity'),
        ('Reading', 'Growth + Creation', 'Read for 30 minutes from your current book'),
        ('Learning', 'Growth + Creation', 'Spend 1 hour learning something new'),
        ('Journaling', 'Purpose + People', 'Write about your thoughts and experiences'),
        ('Connect', 'Purpose + People', 'Reach out to a friend or family member')
    ]
    
    # Insert activities using parameterized queries
    for name, category, description in default_activities:
        # Check if activity exists
        exists = connection.execute(
            sa.text("SELECT id FROM activities WHERE name = :name"),
            {"name": name}
        ).fetchone()
        
        if not exists:
            activity_id = str(uuid.uuid4())
            connection.execute(
                sa.text("""
                INSERT INTO activities (id, name, category, description, xp_value, is_active)
                VALUES (:id, :name, :category, :description, :xp_value, :is_active)
                """),
                {
                    "id": activity_id,
                    "name": name,
                    "category": category,
                    "description": description,
                    "xp_value": 10,
                    "is_active": True
                }
            )

def downgrade():
    connection = op.get_bind()
    
    # Drop the unique constraint
    try:
        op.drop_constraint('unique_user_activity', 'user_activities', type_='unique')
    except Exception as e:
        print(f"Error dropping constraint: {e}")
    
    # Drop the user_activities table
    try:
        op.drop_table('user_activities')
    except Exception as e:
        print(f"Error dropping table: {e}") 