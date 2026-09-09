"""
Authentication Routes — Crime-Watch
==================================
Clean, working authentication implementation
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, decode_token as fjwt_decode
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app import db, limiter
from app.models.models import User, RefreshToken
from app.security.passwords import verify_password
from app.security.totp import verify_totp, generate_totp_secret, get_provisioning_qr_base64
from app.security.audit import write_audit_event
from app.security.decorators import login_required, role_required

# Refresh token TTL for database storage
REFRESH_TOKEN_TTL = timedelta(days=7)

def refresh_token_hash(token: str) -> str:
    """Generate SHA256 hash of refresh token for storage."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """Community self-registration only - role is hardcoded to 'community'."""
    try:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        existing = db.session.query(User).filter_by(email=email).first()
        if existing:
            return jsonify({"error": "Email already registered"}), 409

        user = User(
            name=name or email.split("@")[0],
            email=email,
            role="community",  # hardcoded - no privilege escalation
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        write_audit_event(user.id, "ROLE_CHANGE", metadata={"action": "registration"})

        return jsonify({
            "message": "User registered successfully",
            "user": user.to_dict(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.post("/login")
@limiter.limit("5 per minute")
def login():
    """Login with rate limiting, account lockout, and MFA support."""
    try:
        data = request.get_json(silent=True) or {}
        # Support both "identifier" (new) and "email" (legacy) for backward compatibility
        identifier = data.get("identifier") or data.get("email")  # email OR officer_id
        password = data.get("password")
        totp_code = data.get("totp_code")  # optional unless role requires it

        if not identifier or not password:
            return jsonify({"error": "Email/identifier and password are required"}), 400

        user = User.query.filter(
            (User.email == identifier) | (User.officer_id == identifier)
        ).first()

        # Uniform failure path — do not reveal whether identifier, password, or MFA failed
        def reject(event_type):
            write_audit_event(user.id if user else None, event_type)
            return jsonify({"error": "Invalid credentials"}), 401

        if user is None:
            return reject("LOGIN_FAILED")

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return reject("LOCKOUT")

        if not verify_password(user.password_hash, password):
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.session.commit()
            return reject("LOGIN_FAILED")

        # MFA check — only enforce when the user has actually enrolled TOTP
        if user.totp_enabled:
            if not totp_code or not verify_totp(user.totp_secret, totp_code):
                return reject("MFA_FAILED")

        # Successful login - reset lockout counters
        user.failed_login_count = 0
        user.locked_until = None
        db.session.commit()

        # Use Flask-JWT-Extended for token creation
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role, "type": "access"}
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims={"type": "refresh"}
        )
        refresh_hash = refresh_token_hash(refresh_token)

        db.session.add(RefreshToken(
            user_id=user.id, token_hash=refresh_hash,
            expires_at=datetime.now(timezone.utc) + REFRESH_TOKEN_TTL
        ))
        db.session.commit()

        write_audit_event(user.id, "LOGIN_SUCCESS")
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "role": user.role,
            "user": user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.post("/refresh")
def refresh():
    """Rotate refresh token and issue new access token."""
    try:
        data = request.get_json(silent=True) or {}
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return jsonify({"error": "Refresh token required"}), 400

        try:
            payload = fjwt_decode(refresh_token)
        except ExpiredSignatureError:
            return jsonify({"error": "Refresh token expired"}), 401
        except InvalidTokenError:
            return jsonify({"error": "Invalid refresh token"}), 401

        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            return jsonify({"error": "Invalid token type"}), 401

        user_id = int(payload.get("sub"))
        token_hash = refresh_token_hash(refresh_token)

        # Check if token exists and is not revoked
        stored_token = RefreshToken.query.filter_by(
            user_id=user_id,
            token_hash=token_hash,
            revoked=False
        ).first()

        if not stored_token:
            return jsonify({"error": "Invalid refresh token"}), 401

        # Check for reuse attack (revoked token presented again)
        if stored_token.revoked:
            # Revoke all tokens for this user - potential compromise
            RefreshToken.query.filter_by(user_id=user_id).update({"revoked": True})
            db.session.commit()
            write_audit_event(user_id, "TOKEN_REFRESH", metadata={"compromise_detected": True})
            return jsonify({"error": "Token compromise detected - all tokens revoked"}), 401

        # Rotate the refresh token
        stored_token.revoked = True
        new_refresh_token = create_refresh_token(
            identity=str(user_id),
            additional_claims={"type": "refresh"}
        )
        new_refresh_hash = refresh_token_hash(new_refresh_token)
        db.session.add(RefreshToken(
            user_id=user_id,
            token_hash=new_refresh_hash,
            expires_at=datetime.now(timezone.utc) + REFRESH_TOKEN_TTL
        ))

        # Get user role for new access token
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        new_access_token = create_access_token(
            identity=str(user_id),
            additional_claims={"role": user.role, "type": "access"}
        )
        db.session.commit()

        write_audit_event(user_id, "TOKEN_REFRESH")
        return jsonify({
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500


@auth_bp.post("/logout")
@login_required
def logout():
    """Revoke the presented refresh token."""
    try:
        data = request.get_json(silent=True) or {}
        refresh_token = data.get("refresh_token")

        if refresh_token:
            token_hash = refresh_token_hash(refresh_token)
            stored_token = RefreshToken.query.filter_by(
                user_id=g.user_id,
                token_hash=token_hash,
                revoked=False
            ).first()
            if stored_token:
                stored_token.revoked = True
                db.session.commit()

        write_audit_event(g.user_id, "LOGOUT")
        return jsonify({"message": "Logged out successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500


@auth_bp.get("/me")
@login_required
def get_current_user():
    try:
        user = db.session.get(User, g.user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user.to_dict()})
    except Exception as e:
        return jsonify({"error": f"Failed to get user: {str(e)}"}), 500


@auth_bp.post("/mfa/enroll")
@login_required
def mfa_enroll():
    """Generate TOTP secret and QR code for MFA enrollment."""
    try:
        user = db.session.get(User, g.user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.totp_enabled:
            return jsonify({"error": "MFA already enabled"}), 400

        secret = generate_totp_secret()
        user.totp_secret = secret
        db.session.commit()

        account_name = user.email if user.email else user.officer_id
        qr_base64 = get_provisioning_qr_base64(secret, account_name)

        return jsonify({
            "secret": secret,
            "qr_code": qr_base64,
            "message": "Scan the QR code with your authenticator app, then confirm with /mfa/confirm"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"MFA enrollment failed: {str(e)}"}), 500


@auth_bp.post("/mfa/confirm")
@login_required
def mfa_confirm():
    """Confirm MFA enrollment by verifying first TOTP code."""
    try:
        data = request.get_json(silent=True) or {}
        totp_code = data.get("totp_code")

        if not totp_code:
            return jsonify({"error": "TOTP code required"}), 400

        user = db.session.get(User, g.user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not user.totp_secret:
            return jsonify({"error": "MFA enrollment not started"}), 400

        if user.totp_enabled:
            return jsonify({"error": "MFA already enabled"}), 400

        if not verify_totp(user.totp_secret, totp_code):
            return jsonify({"error": "Invalid TOTP code"}), 400

        user.totp_enabled = True
        db.session.commit()

        write_audit_event(g.user_id, "ROLE_CHANGE", metadata={"mfa_enabled": True})
        return jsonify({"message": "MFA enabled successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"MFA confirmation failed: {str(e)}"}), 500
