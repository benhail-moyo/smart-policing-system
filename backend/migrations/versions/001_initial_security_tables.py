"""Initial security tables

Revision ID: 001_initial_security_tables
Revises: 
Create Date: 2026-08-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_security_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # This migration is a placeholder since db.create_all() was already run
    # The security tables (refresh_tokens, audit_log) and User model updates
    # are already in place via db.create_all()
    pass


def downgrade():
    pass
