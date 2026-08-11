from sqlalchemy import inspect, text

from app import create_app, db


def apply_compatibility_migrations():
    """Apply small, idempotent schema upgrades for installations without Alembic.

    ``create_all`` only creates missing tables; it does not add newly introduced
    columns to an existing database.  Keep this transitional migration here so a
    previously created development Docker volume can start after model changes.
    """
    columns = {column["name"] for column in inspect(db.engine).get_columns("incident")}
    if "occurred_at" not in columns:
        db.session.execute(text("ALTER TABLE incident ADD COLUMN occurred_at TIMESTAMP NULL"))
        db.session.commit()
        print("Applied schema upgrade: incident.occurred_at")

app = create_app()
with app.app_context():
    db.create_all()
    apply_compatibility_migrations()
    print('Database tables created successfully')
