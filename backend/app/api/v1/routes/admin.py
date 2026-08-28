from flask import Blueprint, jsonify, request
from app import db
from app.models.models import User
from app.security.decorators import login_required, role_required
from app.security.totp import generate_totp_secret, get_provisioning_qr_base64

admin_bp = Blueprint("admin", __name__)


@admin_bp.post("/users")
@login_required
@role_required("admin")
def create_user():
    """Create officer or admin accounts (admin only)."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    officer_id = (data.get("officer_id") or "").strip()
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""
    role = data.get("role", "officer").lower()

    # Validation
    if role not in ("officer", "admin"):
        return jsonify({"error": "Invalid role"}), 400

    if not password or len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if role == "officer" and not officer_id:
        return jsonify({"error": "Officer ID required for officer role"}), 400

    if role == "admin" and not email:
        return jsonify({"error": "Email required for admin role"}), 400

    # Check for duplicates
    if email:
        existing = db.session.query(User).filter_by(email=email).first()
        if existing:
            return jsonify({"error": "Email already registered"}), 409

    if officer_id:
        existing = db.session.query(User).filter_by(officer_id=officer_id).first()
        if existing:
            return jsonify({"error": "Officer ID already exists"}), 409

    # Create user
    user = User(
        email=email if email else None,
        officer_id=officer_id if officer_id else None,
        name=name or email or officer_id,
        role=role
    )
    user.set_password(password)

    # Generate TOTP secret for mandatory MFA (officers/admins)
    totp_secret = generate_totp_secret()
    user.totp_secret = totp_secret
    user.totp_enabled = False  # User must complete enrollment

    db.session.add(user)
    db.session.commit()

    # Generate QR code for enrollment
    account_name = user.email if user.email else user.officer_id
    qr_base64 = get_provisioning_qr_base64(totp_secret, account_name, "Crime-Watch")

    return jsonify({
        "message": f"{role.capitalize()} account created successfully",
        "user": user.to_dict(),
        "mfa": {
            "secret": totp_secret,
            "qr_code": qr_base64,
            "instructions": "User must complete MFA enrollment before login"
        }
    }), 201
