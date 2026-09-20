"""Add email OTP table for two-factor authentication

Revision ID: 004_add_email_otp_table
Revises: 003_add_missing_user_security_columns
Create Date: 2026-09-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = '004_add_email_otp_table'
down_revision = '003_add_missing_user_security_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_otp table
    op.create_table(
        'email_otp',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=lambda: datetime.now(timezone.utc)),
        sa.Index('ix_email_otp_user_id', 'user_id'),
        sa.Index('ix_email_otp_code', 'code'),
    )
    
    # Create index for faster expiration cleanup
    op.create_index('ix_email_otp_expires_at', 'email_otp', ['expires_at'])


def downgrade():
    # Drop the email_otp table
    op.drop_index('ix_email_otp_expires_at', 'email_otp')
    op.drop_index('ix_email_otp_code', 'email_otp')
    op.drop_index('ix_email_otp_user_id', 'email_otp')
    op.drop_table('email_otp')