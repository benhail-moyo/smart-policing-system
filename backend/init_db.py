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
        
        # Migration for entity extraction and override fields
        new_columns = ["extracted_entities", "manual_severity", "manual_category", 
                      "override_reason", "override_by_id", "override_at"]
        for new_col in new_columns:
            if new_col not in columns:
                if new_col == "extracted_entities":
                    db.session.execute(text("ALTER TABLE incident ADD COLUMN extracted_entities JSON"))
                elif new_col in ["manual_severity", "manual_category"]:
                    db.session.execute(text(f"ALTER TABLE incident ADD COLUMN {new_col} VARCHAR(120)"))
                elif new_col == "override_reason":
                    db.session.execute(text("ALTER TABLE incident ADD COLUMN override_reason TEXT"))
                elif new_col == "override_by_id":
                    db.session.execute(text("ALTER TABLE incident ADD COLUMN override_by_id INTEGER"))
                elif new_col == "override_at":
                    db.session.execute(text("ALTER TABLE incident ADD COLUMN override_at TIMESTAMP"))
                db.session.commit()
                print(f"Applied schema upgrade: incident.{new_col}")
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
    
    # Migration for multi-vehicle patrol route support
    try:
        patrol_route_table_exists = inspect(db.engine).has_table("patrol_route")
        if patrol_route_table_exists:
            try:
                patrol_route_columns = {column["name"] for column in inspect(db.engine).get_columns("patrol_route")}
                new_columns = ["vehicle_id", "generation_id"]
                for new_col in new_columns:
                    if new_col not in patrol_route_columns:
                        if new_col == "vehicle_id":
                            db.session.execute(text("ALTER TABLE patrol_route ADD COLUMN vehicle_id INTEGER"))
                        elif new_col == "generation_id":
                            db.session.execute(text("ALTER TABLE patrol_route ADD COLUMN generation_id VARCHAR(36)"))
                        db.session.commit()
                        print(f"Applied schema upgrade: patrol_route.{new_col}")
            except Exception as table_error:
                print(f"Note: Could not inspect patrol_route columns: {table_error}")
    except Exception as e:
        print(f"Note: Could not check patrol_route table: {e}")
    
    # Create audit_log table for multi-vehicle route override tracking
    try:
        audit_log_table_exists = inspect(db.engine).has_table("audit_log")
        if not audit_log_table_exists:
            db.session.execute(text("""
                CREATE TABLE audit_log (
                    id SERIAL PRIMARY KEY,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id VARCHAR(100) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    previous_state JSON,
                    new_state JSON,
                    override_reason TEXT,
                    override_by_id INTEGER,
                    vehicle_id INTEGER,
                    generation_id VARCHAR(36),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    FOREIGN KEY (override_by_id) REFERENCES "user"(id)
                )
            """))
            db.session.commit()
            print("Created audit_log table for multi-vehicle route override tracking")
    except Exception as e:
        print(f"Note: Could not create audit_log table: {e}")

app = create_app()
with app.app_context():
    apply_compatibility_migrations()
    db.create_all()
    print('Database tables created successfully')
