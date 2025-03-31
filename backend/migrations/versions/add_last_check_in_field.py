"""add last_check_in field

Revision ID: add_last_check_in_field
Revises: add_custom_activity_fields_v2
Create Date: 2024-03-30 15:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_last_check_in_field'
down_revision = 'add_custom_activity_fields_v2'
branch_labels = None
depends_on = None


def upgrade():
    # Add last_check_in column to users table
    op.add_column('users', sa.Column('last_check_in', sa.Date(), nullable=True))


def downgrade():
    # Remove last_check_in column from users table
    op.drop_column('users', 'last_check_in') 