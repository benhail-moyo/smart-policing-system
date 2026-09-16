from sqlalchemy import inspect, text
from geoalchemy2.shape import to_shape

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
        db_url = str(db.engine.url)
        user_sql_name = '"user"' if 'postgresql' in db_url else 'user'
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
                db.session.execute(text(f"ALTER TABLE {user_sql_name} ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                print(f"Applied schema upgrade: user.{col_name}")

        # Create security tables if they don't exist
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        user_ref = '"user"(id)' if 'postgresql' in db_url else 'user(id)'

        if 'refresh_tokens' not in existing_tables:
            db.session.execute(text(f"""
                CREATE TABLE refresh_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES {user_ref} NOT NULL,
                    token_hash VARCHAR(128) NOT NULL,
                    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    revoked BOOLEAN DEFAULT FALSE
                )
            """))
            db.session.commit()
            print("Created table: refresh_tokens")

        if 'audit_log' not in existing_tables:
            if 'postgresql' in db_url:
                db.session.execute(text(f"""
                    CREATE TABLE audit_log (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES {user_ref},
                        event_type VARCHAR(50) NOT NULL,
                        event_metadata JSONB,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(255),
                        entity_type VARCHAR(50),
                        entity_id VARCHAR(100),
                        action VARCHAR(50),
                        previous_state JSONB,
                        new_state JSONB,
                        override_reason TEXT,
                        override_by_id INTEGER REFERENCES {user_ref},
                        vehicle_id INTEGER,
                        generation_id VARCHAR(36),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT valid_event_type CHECK (event_type IN ('LOGIN_SUCCESS','LOGIN_FAILED','MFA_FAILED','LOCKOUT','ROLE_CHANGE','TOKEN_REFRESH','LOGOUT','ROUTE_OVERRIDE','ENTITY_UPDATE'))
                    )
                """))
            else:
                # SQLite fallback
                db.session.execute(text(f"""
                    CREATE TABLE audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER REFERENCES {user_ref},
                        event_type VARCHAR(50) NOT NULL,
                        event_metadata TEXT,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(255),
                        entity_type VARCHAR(50),
                        entity_id VARCHAR(100),
                        action VARCHAR(50),
                        previous_state TEXT,
                        new_state TEXT,
                        override_reason TEXT,
                        override_by_id INTEGER REFERENCES {user_ref},
                        vehicle_id INTEGER,
                        generation_id VARCHAR(36),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CHECK (event_type IN ('LOGIN_SUCCESS','LOGIN_FAILED','MFA_FAILED','LOCKOUT','ROLE_CHANGE','TOKEN_REFRESH','LOGOUT','ROUTE_OVERRIDE','ENTITY_UPDATE'))
                    )
                """))
            db.session.commit()
            print("Created table: audit_log")
        else:
            # Add missing columns to existing audit_log table
            audit_log_columns = {column["name"] for column in inspect(db.engine).get_columns("audit_log")}
            
            basic_columns = {
                'user_id': f'INTEGER REFERENCES {user_ref}',
                'vehicle_id': 'INTEGER'
            }
            
            for col_name, col_type in basic_columns.items():
                if col_name not in audit_log_columns:
                    db.session.execute(text(f"ALTER TABLE audit_log ADD COLUMN {col_name} {col_type}"))
                    db.session.commit()
                    print(f"Applied schema upgrade: audit_log.{col_name}")
            
            # Entity tracking columns
            entity_tracking_columns = {
                'entity_type': 'VARCHAR(50)',
                'entity_id': 'VARCHAR(100)',
                'action': 'VARCHAR(50)',
                'previous_state': 'JSONB' if 'postgresql' in db_url else 'TEXT',
                'new_state': 'JSONB' if 'postgresql' in db_url else 'TEXT',
                'override_reason': 'TEXT',
                'override_by_id': f'INTEGER REFERENCES {user_ref}',
                'generation_id': 'VARCHAR(36)'
            }

            for col_name, col_type in entity_tracking_columns.items():
                if col_name not in audit_log_columns:
                    db.session.execute(text(f"ALTER TABLE audit_log ADD COLUMN {col_name} {col_type}"))
                    db.session.commit()
                    print(f"Applied schema upgrade: audit_log.{col_name}")

            # Ensure nullable constraints on entity columns for security audit logs
            if 'postgresql' in db_url:
                for col in ['entity_type', 'entity_id', 'action']:
                    try:
                        db.session.execute(text(f"ALTER TABLE audit_log ALTER COLUMN {col} DROP NOT NULL"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

        # Check and add multi-vehicle support columns to patrol_route table
        if 'patrol_route' in existing_tables:
            try:
                patrol_route_columns = {column["name"] for column in inspect(db.engine).get_columns("patrol_route")}
                multi_vehicle_columns = {
                    'vehicle_id': 'INTEGER',
                    'generation_id': 'VARCHAR(36)'
                }

                for col_name, col_type in multi_vehicle_columns.items():
                    if col_name not in patrol_route_columns:
                        db.session.execute(text(f"ALTER TABLE patrol_route ADD COLUMN {col_name} {col_type}"))
                        db.session.commit()
                        print(f"Applied schema upgrade: patrol_route.{col_name}")
            except Exception as e:
                print(f"Warning during patrol_route multi-vehicle migration: {e}")

        # Check and update hotspot table schema if using old schema
        if 'hotspot' in existing_tables:
            try:
                hotspot_columns = {column["name"] for column in inspect(db.engine).get_columns("hotspot")}
                # Check if using old schema (has 'id' instead of 'hotspot_id', or missing lat/lng)
                if 'id' in hotspot_columns and 'hotspot_id' not in hotspot_columns:
                    print("Detected old hotspot schema (id column). Dropping and recreating hotspot table...")
                    db.session.execute(text("DROP TABLE IF EXISTS hotspot_history"))
                    db.session.execute(text("DROP TABLE IF EXISTS hotspot"))
                    db.session.commit()
                    print("Old hotspot tables dropped. Will be recreated with new schema.")
                elif 'lat' not in hotspot_columns or 'lng' not in hotspot_columns:
                    print("Detected old hotspot schema (missing lat/lng). Dropping and recreating hotspot table...")
                    db.session.execute(text("DROP TABLE IF EXISTS hotspot_history"))
                    db.session.execute(text("DROP TABLE IF EXISTS hotspot"))
                    db.session.commit()
                    print("Old hotspot tables dropped. Will be recreated with new schema.")
            except Exception as e:
                print(f"Warning during hotspot schema migration: {e}")

    except Exception as e:
        print(f"Warning during schema migrations: {e}")
        # Continue anyway - the main create_all() will handle new installations

app = create_app()
with app.app_context():
    apply_compatibility_migrations()
    db.create_all()
    print('Database tables created successfully')
