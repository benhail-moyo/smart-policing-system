#!/usr/bin/env python
"""Test script to verify database migration was successful."""
from app import create_app
from app.models.models import PatrolRoute, AuditLog

app = create_app()

with app.app_context():
    print("PatrolRoute columns:", [col.name for col in PatrolRoute.__table__.columns])
    print("AuditLog columns:", [col.name for col in AuditLog.__table__.columns])
    
    # Check if new columns exist
    patrol_columns = [col.name for col in PatrolRoute.__table__.columns]
    audit_columns = [col.name for col in AuditLog.__table__.columns]
    
    print("\nMigration verification:")
    print(f"vehicle_id in PatrolRoute: {'vehicle_id' in patrol_columns}")
    print(f"generation_id in PatrolRoute: {'generation_id' in patrol_columns}")
    print(f"vehicle_id in AuditLog: {'vehicle_id' in audit_columns}")
    
    if 'vehicle_id' in patrol_columns and 'generation_id' in patrol_columns and 'vehicle_id' in audit_columns:
        print("\n[SUCCESS] Database migration successful!")
    else:
        print("\n[ERROR] Database migration incomplete!")