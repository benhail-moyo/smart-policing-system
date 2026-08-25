import pytest
from app import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Create a new database session for a test."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        
        # Bind the session to the connection
        session = _db.create_scoped_session(options={"bind": connection})
        
        _db.session = session
        
        yield session
        
        # Cleanup
        session.close()
        transaction.rollback()
        connection.close()
