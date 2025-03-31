"""merge activities migrations

Revision ID: merge_activities_migrations
Revises: add_activities_columns, add_custom_activity_fields
Create Date: 2024-03-30 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_activities_migrations'
down_revision = ('add_activities_columns', 'add_custom_activity_fields')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass 