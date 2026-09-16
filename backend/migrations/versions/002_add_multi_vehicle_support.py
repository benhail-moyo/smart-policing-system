"""Add multi-vehicle support to patrol routes and audit log

Revision ID: 002_add_multi_vehicle_support
Revises: 001_initial_security_tables
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_multi'
down_revision = '001_sec'
branch_labels = None
depends_on = None


def upgrade():
    # Add multi-vehicle support columns to patrol_route table
    # Check if vehicle_id already exists to avoid conflicts
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('patrol_route')]
    
    if 'vehicle_id' not in columns:
        op.add_column('patrol_route', sa.Column('vehicle_id', sa.Integer(), nullable=True))
    
    if 'generation_id' not in columns:
        op.add_column('patrol_route', sa.Column('generation_id', sa.String(36), nullable=True))
    
    # Add vehicle_id to audit_log for route override tracking
    audit_columns = [col['name'] for col in inspector.get_columns('audit_log')]
    if 'vehicle_id' not in audit_columns:
        op.add_column('audit_log', sa.Column('vehicle_id', sa.Integer(), nullable=True))


def downgrade():
    # Remove multi-vehicle support columns
    op.drop_column('audit_log', 'vehicle_id')
    op.drop_column('patrol_route', 'generation_id')
    op.drop_column('patrol_route', 'vehicle_id')
