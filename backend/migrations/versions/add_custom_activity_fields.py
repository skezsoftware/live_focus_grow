"""add custom activity fields

Revision ID: add_custom_activity_fields
Revises: add_missing_columns
Create Date: 2024-03-30 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

# revision identifiers, used by Alembic.
revision = 'add_custom_activity_fields'
down_revision = 'add_missing_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to activities table
    op.add_column('activities', sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('activities', sa.Column('is_custom', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('activities', sa.Column('type', sa.String(50), nullable=True))

    # Add index for faster lookups
    op.create_index(op.f('ix_activities_user_id'), 'activities', ['user_id'], unique=False)
    op.create_index(op.f('ix_activities_is_custom'), 'activities', ['is_custom'], unique=False)

def downgrade():
    # Remove indexes
    op.drop_index(op.f('ix_activities_is_custom'), table_name='activities')
    op.drop_index(op.f('ix_activities_user_id'), table_name='activities')

    # Remove columns
    op.drop_column('activities', 'type')
    op.drop_column('activities', 'is_custom')
    op.drop_column('activities', 'user_id') 