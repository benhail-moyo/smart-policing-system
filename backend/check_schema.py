from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    print('Tables:', inspector.get_table_names())
    if 'hotspot' in inspector.get_table_names():
        print('Hotspot columns:', [col['name'] for col in inspector.get_columns('hotspot')])
