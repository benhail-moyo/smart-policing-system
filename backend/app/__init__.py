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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from dotenv import load_dotenv
import os
import logging

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Configure limiter with robust error handling
def get_identifier():
    """Get request identifier with fallback for rate limiting."""
    try:
        return get_remote_address()
    except Exception:
        return "unknown"

limiter = Limiter(
    key_func=get_identifier,
    strategy="fixed-window",
    swallow_errors=True
)


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory.

    Args:
        config_name: One of 'development', 'testing', 'production'

    Returns:
        Configured Flask application instance.
    """
    # Load environment variables from .env file (in project root)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    load_dotenv(os.path.join(project_root, '.env'))
    
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
    
    # Initialize limiter with proper error handling
    try:
        limiter.init_app(app)
    except Exception as e:
        app.logger.warning(f"Rate limiter initialization failed: {e}. Rate limiting will be disabled.")
    
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # Tighten in production
    
    # Configure GeoAlchemy2 for SQLite compatibility
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SPADEQA'] = False

    # ── Register blueprints (API routes) ────────────────────────────────────
    from app.api.v1.routes.incidents import incidents_bp
    from app.api.v1.routes.hotspots import hotspots_bp
    from app.api.v1.routes.patrol import patrol_bp
    from app.api.v1.routes.auth import auth_bp
    from app.api.v1.routes.analysis import analysis_bp
    from app.api.v1.routes.seed import seed_bp
    from app.api.v1.routes.command import command_bp
    from app.api.v1.routes.admin import admin_bp

    app.register_blueprint(auth_bp,      url_prefix="/api/v1/auth")
    app.register_blueprint(incidents_bp, url_prefix="/api/v1/incidents")
    app.register_blueprint(hotspots_bp,  url_prefix="/api/v1/hotspots")
    app.register_blueprint(patrol_bp,    url_prefix="/api/v1/patrol")
    app.register_blueprint(analysis_bp,  url_prefix="/api/v1/analysis")
    app.register_blueprint(seed_bp,      url_prefix="/api/v1/seed")
    app.register_blueprint(command_bp,   url_prefix="/api/v1/command")
    app.register_blueprint(admin_bp,     url_prefix="/api/v1/admin")

    # ── Health check ─────────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "crime-watch-api"}, 200

    # Global JSON error handlers
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(err):
        """Handle rate limit errors gracefully."""
        app.logger.warning(f"Rate limit exceeded: {err.description}")
        return {
            "error": "Rate limit exceeded",
            "details": str(err.description),
            "retry_after": getattr(err, 'retry_after', None)
        }, 429

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return {"error": err.name, "details": err.description}, err.code

    @app.errorhandler(Exception)
    def handle_exception(err):
        # Let Flask log the exception as usual, but return a JSON payload
        app.logger.exception("Unhandled exception: %s", err)
        return {"error": "Internal server error", "details": str(err)}, 500

    # ── CLI Commands ─────────────────────────────────────────────────────────
    @app.cli.command("create-admin")
    def create_admin():
        """Create the initial admin account via CLI."""
        from app.models.models import User
        from app.security.totp import generate_totp_secret, get_provisioning_qr_base64

        print("=== Create Initial Admin Account ===")
        email = input("Admin email: ").strip()
        if not email:
            print("Email is required")
            return

        password = input("Password: ")
        if not password or len(password) < 8:
            print("Password must be at least 8 characters")
            return

        confirm_password = input("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match")
            return

        # Check if admin already exists
        existing = db.session.query(User).filter_by(email=email).first()
        if existing:
            print(f"Admin with email {email} already exists")
            return

        # Create admin with mandatory MFA
        admin = User(
            email=email,
            role="admin",
            name="System Administrator"
        )
        admin.set_password(password)

        # Generate TOTP secret for mandatory MFA
        totp_secret = generate_totp_secret()
        admin.totp_secret = totp_secret
        admin.totp_enabled = True  # Admins must have MFA enabled

        db.session.add(admin)
        db.session.commit()

        # Generate QR code for easy setup
        qr_base64 = get_provisioning_qr_base64(totp_secret, email, "Crime-Watch")

        print(f"\n✓ Admin account created successfully!")
        print(f"  Email: {email}")
        print(f"  Role: admin")
        print(f"  MFA: Enabled (mandatory for admins)")
        print(f"\nIMPORTANT: Scan this QR code with your authenticator app:")
        print(f"  (QR code data: {qr_base64[:50]}...)")
        print(f"\nOr manually enter this TOTP secret:")
        print(f"  {totp_secret}")
        print(f"\nYou will need to complete MFA setup before logging in.")

    return app

