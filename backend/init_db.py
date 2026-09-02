from sqlalchemy import inspect, text
from geoalchemy2.shape import to_shape

from app import create_app, db


def apply_compatibility_migrations():
    """Apply small, idempotent schema upgrades for installations without Alembic.

    ``create_all`` only creates missing tables; it does not add newly introduced
    columns to an existing database.  Keep this transitional migration here so a
    previously created development Docker volume can start after model changes.
    """
    # First, ensure PostGIS extension is created before any other operations
    try:
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        db.session.commit()
        print("PostGIS extension enabled")
    except Exception as e:
        print(f"Warning: PostGIS extension setup failed: {e}")
        print("Ensure your database has PostGIS installed")
    
    # Migration for incident.occurred_at
    try:
        columns = {column["name"] for column in inspect(db.engine).get_columns("incident")}
        if "occurred_at" not in columns:
            db.session.execute(text("ALTER TABLE incident ADD COLUMN occurred_at TIMESTAMP NULL"))
            db.session.commit()
            print("Applied schema upgrade: incident.occurred_at")
    except Exception as e:
        print(f"Note: Could not upgrade incident table: {e}")
    
    # Fresh start migration for hotspot tables with PostGIS
    try:
        hotspot_table_exists = inspect(db.engine).has_table("hotspot")
        if hotspot_table_exists:
            # Check if old hotspot table exists (with lat/lng columns or integer id)
            hotspot_columns = {column["name"] for column in inspect(db.engine).get_columns("hotspot")}
            
            # Check for old schema indicators
            has_old_location = "lat" in hotspot_columns and "lng" in hotspot_columns
            has_integer_id = "id" in hotspot_columns and "hotspot_id" not in hotspot_columns
            
            if has_old_location or has_integer_id:
                print("Detected old hotspot schema - performing fresh start migration")
                # Drop old tables
                db.session.execute(text("DROP TABLE IF EXISTS hotspot CASCADE"))
                db.session.execute(text("DROP TABLE IF EXISTS hotspot_history CASCADE"))
                db.session.commit()
                print("Dropped old hotspot tables for fresh start")
    except Exception as e:
        print(f"Note: Could not check hotspot columns (table may not exist yet): {e}")
    
    # Create spatial index on hotspot centroid if table exists
    try:
        hotspot_table_exists = inspect(db.engine).has_table("hotspot")
        if hotspot_table_exists:
            # Check if spatial index already exists
            index_exists = False
            try:
                indexes = inspect(db.engine).get_indexes("hotspot")
                index_exists = any(idx["name"] == "idx_hotspot_centroid" for idx in indexes)
            except:
                pass
            
            if not index_exists:
                db.session.execute(text("CREATE INDEX idx_hotspot_centroid ON hotspot USING GIST (centroid)"))
                db.session.commit()
                print("Created spatial index on hotspot.centroid")
    except Exception as e:
        print(f"Note: Spatial index creation: {e}")

app = create_app()
with app.app_context():
    apply_compatibility_migrations()
    db.create_all()
    print('Database tables created successfully')
