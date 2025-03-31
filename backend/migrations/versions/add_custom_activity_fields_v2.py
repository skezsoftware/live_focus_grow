"""add custom activity fields v2

Revision ID: add_custom_activity_fields_v2
Revises: merge_activities_migrations
Create Date: 2024-03-30 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers, used by Alembic.
revision = 'add_custom_activity_fields_v2'
down_revision = 'merge_activities_migrations'
branch_labels = None
depends_on = None

def upgrade():
    # Since user_id and is_custom already exist, we'll just add type if it doesn't exist
    # First check if type column exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('activities')]
    
    if 'type' not in columns:
        op.add_column('activities', sa.Column('type', sa.String(50), nullable=True))

    # Add the "balls" activity if it doesn't exist
    activity_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    
    conn.execute(
        sa.text("""
        INSERT INTO activities (id, user_id, name, category, type, is_custom, is_active, created_at, xp_value)
        SELECT 
            :id,
            (SELECT id FROM users WHERE email = 'test5@email.com' LIMIT 1),
            'Balls',
            'Mind + Body',
            'custom',
            TRUE,
            TRUE,
            :created_at,
            100
        WHERE NOT EXISTS (
            SELECT 1 FROM activities 
            WHERE name = 'Balls' 
            AND user_id = (SELECT id FROM users WHERE email = 'test5@email.com' LIMIT 1)
        )
        """),
        {"id": activity_id, "created_at": created_at}
    )

def downgrade():
    # Only drop the type column if we added it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('activities')]
    
    if 'type' in columns:
        op.drop_column('activities', 'type') 