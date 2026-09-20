"""Add missing user security columns

Revision ID: 003_add_missing_user_security_columns
Revises: 002_add_multi_vehicle_support
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_user_sec'
down_revision = '002_multi'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing security columns to user table
    op.add_column('user', sa.Column('officer_id', sa.String(50), nullable=True))
    op.add_column('user', sa.Column('totp_secret', sa.String(64), nullable=True))
    op.add_column('user', sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user', sa.Column('failed_login_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('locked_until', sa.DateTime(), nullable=True))
    
    # Create index on officer_id
    op.create_index('ix_user_officer_id', 'user', ['officer_id'])
    
    # Make email column nullable (as per model definition)
    op.alter_column('user', 'email', nullable=True)
    
    # Remove the unique constraint on email since it's now nullable
    op.drop_constraint('user_email_key', 'user', type_='unique')


def downgrade():
    # Remove the index on officer_id
    op.drop_index('ix_user_officer_id', 'user')
    
    # Remove the security columns
    op.drop_column('user', 'locked_until')
    op.drop_column('user', 'failed_login_count')
    op.drop_column('user', 'totp_enabled')
    op.drop_column('user', 'totp_secret')
    op.drop_column('user', 'officer_id')
    
    # Make email column not null and add unique constraint back
    op.alter_column('user', 'email', nullable=False)
    op.create_unique_constraint('user_email_key', 'user', ['email'])
