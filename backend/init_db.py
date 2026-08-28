from sqlalchemy import inspect, text

from app import create_app, db


def apply_compatibility_migrations():
    """Apply small, idempotent schema upgrades for installations without Alembic.

    ``create_all`` only creates missing tables; it does not add newly introduced
    columns to an existing database.  Keep this transitional migration here so a
    previously created development Docker volume can start after model changes.
    """
    # Apply security-related migrations for existing databases
    try:
        # Check and add incident.occurred_at if missing
        columns = {column["name"] for column in inspect(db.engine).get_columns("incident")}
        if "occurred_at" not in columns:
            db.session.execute(text("ALTER TABLE incident ADD COLUMN occurred_at TIMESTAMP NULL"))
            db.session.commit()
            print("Applied schema upgrade: incident.occurred_at")

        # Check and add security columns to user table if missing
        user_columns = {column["name"] for column in inspect(db.engine).get_columns("user")}
        security_columns = {
            'officer_id': 'VARCHAR(50)',
            'totp_secret': 'VARCHAR(64)',
            'totp_enabled': 'BOOLEAN DEFAULT FALSE',
            'failed_login_count': 'INTEGER DEFAULT 0',
            'locked_until': 'TIMESTAMP NULL'
        }

        for col_name, col_type in security_columns.items():
            if col_name not in user_columns:
                db.session.execute(text(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                print(f"Applied schema upgrade: user.{col_name}")

        # Create security tables if they don't exist
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if 'refresh_tokens' not in existing_tables:
            db.session.execute(text("""
                CREATE TABLE refresh_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES user(id) NOT NULL,
                    token_hash VARCHAR(128) NOT NULL,
                    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    revoked BOOLEAN DEFAULT FALSE
                )
            """))
            db.session.commit()
            print("Created table: refresh_tokens")

        if 'audit_log' not in existing_tables:
            # Check if using PostgreSQL (for JSONB support) or SQLite
            db_url = str(db.engine.url)
            if 'postgresql' in db_url:
                db.session.execute(text("""
                    CREATE TABLE audit_log (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES user(id),
                        event_type VARCHAR(50) NOT NULL,
                        event_metadata JSONB,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(255),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT valid_event_type CHECK (event_type IN ('LOGIN_SUCCESS','LOGIN_FAILED','MFA_FAILED','LOCKOUT','ROLE_CHANGE','TOKEN_REFRESH','LOGOUT'))
                    )
                """))
            else:
                # SQLite fallback
                db.session.execute(text("""
                    CREATE TABLE audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER REFERENCES user(id),
                        event_type VARCHAR(50) NOT NULL,
                        event_metadata TEXT,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(255),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CHECK (event_type IN ('LOGIN_SUCCESS','LOGIN_FAILED','MFA_FAILED','LOCKOUT','ROLE_CHANGE','TOKEN_REFRESH','LOGOUT'))
                    )
                """))
            db.session.commit()
            print("Created table: audit_log")

    except Exception as e:
        print(f"Warning during schema migrations: {e}")
        # Continue anyway - the main create_all() will handle new installations

app = create_app()
with app.app_context():
    db.create_all()
    apply_compatibility_migrations()
    print('Database tables created successfully')
