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

# ── Rate Limiter Stub / Configuration ──────────────────────────────────────────
# Stubbed by default to avoid unnecessary rate limit blocks (e.g. 429 errors).
# Can be toggled via RATELIMIT_ENABLED=true in the environment.

class LimiterStub:
    """No-op limiter stub that acts as a passthrough for decorators."""
    def __init__(self, *args, **kwargs):
        self.enabled = False

    def init_app(self, app):
        pass

    def limit(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

    def shared_limit(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

    def exempt(self, f):
        return f


def get_identifier():
    """Get request identifier with fallback for rate limiting."""
    try:
        return get_remote_address()
    except Exception:
        return "unknown"


_rate_limit_enabled = os.getenv("RATELIMIT_ENABLED", "false").lower() in ("true", "1")

if _rate_limit_enabled:
    limiter = Limiter(
        key_func=get_identifier,
        strategy="fixed-window",
        swallow_errors=True
    )
else:
    limiter = LimiterStub()


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory.

    Args:
        config_name: One of 'development', 'testing', 'production'

    Returns:
        Configured Flask application instance.
    """
    # Load environment variables from .env file (search root, backend, and cwd)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    backend_root = os.path.dirname(os.path.dirname(__file__))
    load_dotenv(os.path.join(project_root, '.env'), override=True)
    load_dotenv(os.path.join(backend_root, '.env'), override=True)
    load_dotenv(override=True)
    
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
        from app.security.passwords import validate_password_strength, validate_force_number

        print("=== Create Initial Admin Account ===")
        force_number = input("Admin Force Number (e.g. 000101A): ").strip().upper()
        fn_valid, fn_err = validate_force_number(force_number)
        if not fn_valid:
            print(f"Error: {fn_err}")
            return

        email = input("Admin Email (for 2FA OTP codes): ").strip().lower()
        if not email:
            print("Email is required")
            return

        name = input("Admin Full Name: ").strip() or "System Administrator"

        password = input("Password: ")
        pw_valid, pw_errs = validate_password_strength(password, {"name": name, "email": email, "force_number": force_number})
        if not pw_valid:
            print(f"Password Error: {pw_errs[0]}")
            return

        confirm_password = input("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match")
            return

        # Check if admin already exists
        existing_email = db.session.query(User).filter_by(email=email).first()
        if existing_email:
            print(f"Admin with email {email} already exists")
            return

        existing_fn = db.session.query(User).filter(
            (User.force_number == force_number) | (User.officer_id == force_number)
        ).first()
        if existing_fn:
            print(f"Admin with Force Number {force_number} already exists")
            return

        # Create admin
        admin = User(
            email=email,
            force_number=force_number,
            officer_id=force_number,
            role="admin",
            name=name
        )
        admin.set_password(password)

        # Generate TOTP secret for mandatory MFA
        totp_secret = generate_totp_secret()
        admin.totp_secret = totp_secret
        admin.totp_enabled = True

        db.session.add(admin)
        db.session.commit()

        # Generate QR code for easy setup
        qr_base64 = get_provisioning_qr_base64(totp_secret, force_number, "Crime-Watch")

        print(f"\n✓ Admin account created successfully!")
        print(f"  Force Number: {force_number}")
        print(f"  Email: {email}")
        print(f"  Role: admin")
        print(f"  MFA: Enabled")
        print(f"\nIMPORTANT: Scan this QR code with your authenticator app:")
        print(f"  (QR code data: {qr_base64[:50]}...)")
        print(f"\nOr manually enter this TOTP secret:")
        print(f"  {totp_secret}")

    return app

