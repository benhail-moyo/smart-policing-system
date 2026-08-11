"""
Crime-Watch Flask Application Factory
======================================
Uses the app factory pattern so that different configurations
(development, testing, production) can be loaded without
re-importing the whole app. Essential for pytest.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory.

    Args:
        config_name: One of 'development', 'testing', 'production'

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load config object based on environment
    from app.config.settings import config_map
    app.config.from_object(config_map[config_name])

    # ── Initialize extensions ────────────────────────────────────────────────
    db.init_app(app)

    # Import models BEFORE migrate.init_app so Flask-Migrate discovers all tables
    with app.app_context():
        from app.models import models  # noqa: F401 — registers models with SQLAlchemy

    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # Tighten in production

    # ── Register blueprints (API routes) ────────────────────────────────────
    from app.api.v1.routes.incidents import incidents_bp
    from app.api.v1.routes.hotspots import hotspots_bp
    from app.api.v1.routes.patrol import patrol_bp
    from app.api.v1.routes.auth import auth_bp
    from app.api.v1.routes.analysis import analysis_bp
    from app.api.v1.routes.seed import seed_bp
    from app.api.v1.routes.command import command_bp

    app.register_blueprint(auth_bp,      url_prefix="/api/v1/auth")
    app.register_blueprint(incidents_bp, url_prefix="/api/v1/incidents")
    app.register_blueprint(hotspots_bp,  url_prefix="/api/v1/hotspots")
    app.register_blueprint(patrol_bp,    url_prefix="/api/v1/patrol")
    app.register_blueprint(analysis_bp,  url_prefix="/api/v1/analysis")
    app.register_blueprint(seed_bp,      url_prefix="/api/v1/seed")
    app.register_blueprint(command_bp,   url_prefix="/api/v1/command")

    # ── Health check ─────────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "crime-watch-api"}, 200

    # Global JSON error handler to ensure API returns JSON on uncaught exceptions
    @app.errorhandler(Exception)
    def handle_exception(err):
        # Let Flask log the exception as usual, but return a JSON payload
        app.logger.exception("Unhandled exception: %s", err)
        return ({"error": "Internal server error", "details": str(err)}, 500)
    return app

