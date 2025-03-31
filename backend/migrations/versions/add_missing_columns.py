"""add missing columns to user_activities

Revision ID: add_missing_columns
Revises: update_activities_schema
Create Date: 2024-03-30

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'add_missing_columns'
down_revision = 'update_activities_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Add missing columns to user_activities table
    op.add_column('user_activities', sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_activities', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Update existing rows to set updated_at to current timestamp
    op.execute("UPDATE user_activities SET updated_at = created_at WHERE updated_at IS NULL")

def downgrade():
    # Remove the columns we added
    op.drop_column('user_activities', 'completed')
    op.drop_column('user_activities', 'updated_at') 