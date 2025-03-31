"""add date to user activities

Revision ID: add_date_to_user_activities
Revises: add_last_check_in_field
Create Date: 2024-03-30 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = 'add_date_to_user_activities'
down_revision = 'add_last_check_in_field'
branch_labels = None
depends_on = None


def upgrade():
    # Add date column to user_activities table
    op.add_column('user_activities', sa.Column('date', sa.Date(), nullable=True))
    
    # Update existing records to use created_at date
    op.execute("""
        UPDATE user_activities 
        SET date = DATE(created_at) 
        WHERE date IS NULL
    """)
    
    # Make date column not nullable after setting default values
    op.alter_column('user_activities', 'date',
                    existing_type=sa.Date(),
                    nullable=False)


def downgrade():
    # Remove date column from user_activities table
    op.drop_column('user_activities', 'date') 