from flask import Blueprint, jsonify, request
from app import db
from app.models.models import User
from app.security.decorators import login_required, role_required
from app.security.passwords import validate_password_strength, validate_force_number
from app.security.totp import generate_totp_secret, get_provisioning_qr_base64

admin_bp = Blueprint("admin", __name__)


@admin_bp.post("/users")
@login_required
@role_required("admin")
def create_user():
    """Create officer or admin accounts (admin only)."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    raw_force_number = (data.get("force_number") or data.get("officer_id") or "").strip()
    force_number = raw_force_number.upper() if raw_force_number else ""
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""
    role = data.get("role", "officer").lower()

    # Validation
    if role not in ("officer", "admin"):
        return jsonify({"error": "Invalid role"}), 400

    if not force_number:
        return jsonify({"error": "Force Number is required for police officers and administrators"}), 400

    fn_valid, fn_err = validate_force_number(force_number)
    if not fn_valid:
        return jsonify({"error": fn_err}), 400

    if not email:
        return jsonify({"error": "Official email address is required for 2FA OTP codes"}), 400

    # Password strength check
    user_ctx = {"name": name, "email": email, "force_number": force_number}
    pw_valid, pw_errors = validate_password_strength(password, user_ctx)
    if not pw_valid:
        return jsonify({"error": pw_errors[0], "details": pw_errors}), 400

    # Check for duplicates
    if email:
        existing = db.session.query(User).filter_by(email=email).first()
        if existing:
            return jsonify({"error": "Email already registered"}), 409

    if force_number:
        existing = db.session.query(User).filter(
            (User.force_number == force_number) | (User.officer_id == force_number)
        ).first()
        if existing:
            return jsonify({"error": "Force Number already exists"}), 409

    # Create user
    user = User(
        email=email,
        force_number=force_number,
        officer_id=force_number,
        name=name or email or force_number,
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
