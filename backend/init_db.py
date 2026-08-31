from sqlalchemy import inspect, text

from app import create_app, db


def apply_compatibility_migrations():
    """Apply small, idempotent schema upgrades for installations without Alembic.

    ``create_all`` only creates missing tables; it does not add newly introduced
    columns to an existing database.  Keep this transitional migration here so a
    previously created development Docker volume can start after model changes.
    """
    # Migration for incident.occurred_at
    columns = {column["name"] for column in inspect(db.engine).get_columns("incident")}
    if "occurred_at" not in columns:
        db.session.execute(text("ALTER TABLE incident ADD COLUMN occurred_at TIMESTAMP NULL"))
        db.session.commit()
        print("Applied schema upgrade: incident.occurred_at")
    
    # Migration for hotspot.lat and hotspot.lng
    try:
        hotspot_columns = {column["name"] for column in inspect(db.engine).get_columns("hotspot")}
        if "lat" not in hotspot_columns:
            db.session.execute(text("ALTER TABLE hotspot ADD COLUMN lat REAL NULL"))
            db.session.commit()
            print("Applied schema upgrade: hotspot.lat")
        if "lng" not in hotspot_columns:
            db.session.execute(text("ALTER TABLE hotspot ADD COLUMN lng REAL NULL"))
            db.session.commit()
            print("Applied schema upgrade: hotspot.lng")
    except Exception as e:
        print(f"Note: Could not check hotspot columns (table may not exist yet): {e}")

app = create_app()
with app.app_context():
    db.create_all()
    apply_compatibility_migrations()
    print('Database tables created successfully')
