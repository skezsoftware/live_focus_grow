"""merge heads

Revision ID: e45b622a4332
Revises: add_completed_today_column, add_date_to_user_activities
Create Date: 2025-03-31 11:26:18.668964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e45b622a4332'
down_revision = ('add_completed_today_column', 'add_date_to_user_activities')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
