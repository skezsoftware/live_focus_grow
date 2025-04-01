"""add is_completed_today column

Revision ID: add_completed_today_column
Revises: add_activities_columns
Create Date: 2024-03-31
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_completed_today_column'
down_revision = 'add_activities_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add is_completed_today column with a default value of False
    op.add_column('user_activities', 
        sa.Column('is_completed_today', sa.Boolean(), nullable=False, server_default='false')
    )

def downgrade():
    # Remove is_completed_today column
    op.drop_column('user_activities', 'is_completed_today') 