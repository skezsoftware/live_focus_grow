"""add missing columns to activities

Revision ID: add_activities_columns
Revises: add_missing_columns
Create Date: 2024-03-30

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'add_activities_columns'
down_revision = 'add_missing_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add created_at column to activities table
    op.add_column('activities', sa.Column('created_at', sa.DateTime(), nullable=True))
    
    # Set created_at to current timestamp for existing rows
    op.execute("UPDATE activities SET created_at = NOW() WHERE created_at IS NULL")
    
    # Insert default activities if they don't exist
    op.execute("""
    INSERT INTO activities (id, name, category, description, xp_value, is_active, created_at)
    SELECT 
        md5(random()::text)::uuid::text,
        name,
        category,
        description,
        10,
        true,
        NOW()
    FROM (VALUES 
        ('Morning Meditation', 'Mind + Body', 'Start your day with a 10-minute meditation session'),
        ('Daily Exercise', 'Mind + Body', 'Complete 30 minutes of physical activity'),
        ('Reading', 'Growth + Creation', 'Read for 30 minutes from your current book'),
        ('Learning', 'Growth + Creation', 'Spend 1 hour learning something new'),
        ('Journaling', 'Purpose + People', 'Write about your thoughts and experiences'),
        ('Connect', 'Purpose + People', 'Reach out to a friend or family member')
    ) AS t(name, category, description)
    WHERE NOT EXISTS (
        SELECT 1 FROM activities WHERE name = t.name
    );
    """)

def downgrade():
    # Remove the columns we added
    op.drop_column('activities', 'created_at') 