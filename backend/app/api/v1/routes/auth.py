"""
Authentication Routes — Crime-Watch
==================================
Clean, working authentication implementation
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, decode_token as fjwt_decode
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app import db, limiter
from app.models.models import User, RefreshToken
from app.security.passwords import verify_password, validate_password_strength, validate_force_number
from app.security.totp import verify_totp, generate_totp_secret, get_provisioning_qr_base64
from app.security.audit import write_audit_event
from app.security.decorators import login_required, role_required
from app.services.otp_service import otp_service

# Refresh token TTL for database storage
REFRESH_TOKEN_TTL = timedelta(days=7)

def refresh_token_hash(token: str) -> str:
    """Generate SHA256 hash of refresh token for storage."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


def mask_email(email: str) -> str:
    """Mask email for secure display (e.g. j***e@domain.com)."""
    if not email or "@" not in email:
        return "your registered email"
    user_part, domain = email.split("@", 1)
    if len(user_part) <= 2:
        masked_user = user_part[0] + "***"
    else:
        masked_user = user_part[0] + "***" + user_part[-1]
    return f"{masked_user}@{domain}"


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """Registration endpoint for Community Members and Police Officers."""
    try:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        role = (data.get("role") or "community").strip().lower()
        raw_force_number = data.get("force_number") or data.get("officer_id") or ""
        clean_fn = raw_force_number.strip().upper() if raw_force_number else None

        if role not in ("community", "officer"):
            return jsonify({"error": "Invalid role specified"}), 400

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if role == "officer":
            if not clean_fn:
                return jsonify({"error": "Force Number is required for police officers"}), 400
            fn_valid, fn_err = validate_force_number(clean_fn)
            if not fn_valid:
                return jsonify({"error": fn_err}), 400

        # Validate password strength with organizational 5-rule policy
        user_ctx = {
            "name": name,
            "email": email,
            "force_number": clean_fn if role == "officer" else None
        }
        pw_valid, pw_errors = validate_password_strength(password, user_ctx)
        if not pw_valid:
            return jsonify({"error": pw_errors[0], "details": pw_errors}), 400

        # Check existing email
        existing_email = db.session.query(User).filter_by(email=email).first()
        if existing_email:
            return jsonify({"error": "Email already registered"}), 409

        # Check existing force number if registering as officer
        if role == "officer" and clean_fn:
            existing_fn = db.session.query(User).filter(
                (User.force_number == clean_fn) | (User.officer_id == clean_fn)
            ).first()
            if existing_fn:
                return jsonify({"error": "Force Number already registered"}), 409

        user = User(
            name=name or (email.split("@")[0] if role == "community" else clean_fn),
            email=email,
            force_number=clean_fn if role == "officer" else None,
            officer_id=clean_fn if role == "officer" else None,
            role=role,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        write_audit_event(user.id, "ROLE_CHANGE", metadata={"action": "registration", "role": role})

        return jsonify({
            "message": "User registered successfully",
            "user": user.to_dict(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.post("/verify-email")
def verify_email():
    """Verify email address during registration with OTP."""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        otp_code = data.get("otp_code") or ""

        if not email or not otp_code:
            return jsonify({"error": "Email and OTP code are required"}), 400

        user = db.session.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        is_valid, error_msg = otp_service.verify_otp(user.id, otp_code)
        if not is_valid:
            return jsonify({"error": error_msg or "Invalid OTP code"}), 401

        write_audit_event(user.id, "EMAIL_VERIFIED")

        return jsonify({
            "message": "Email verified successfully",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Email verification failed: {str(e)}"}), 500


@auth_bp.post("/send-verification-email")
def send_verification_email():
    """Send verification email to user."""
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()

        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = db.session.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        success_msg, error_msg = otp_service.generate_otp(user.id)
        if error_msg:
            return jsonify({"error": f"Failed to send verification email: {error_msg}"}), 500

        write_audit_event(user.id, "VERIFICATION_EMAIL_SENT")

        return jsonify({
            "message": success_msg,
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to send verification email: {str(e)}"}), 500


@auth_bp.post("/login")
@limiter.limit("10 per minute", error_message="Too many login attempts. Please try again later.")
def login():
    """
    Login endpoint:
    - Police Officers & Admins: MUST log in with Force Number (format: 123456X) + password.
      Triggers SMTP OTP verification code sent to the email tied to their account.
    - Community Members: Log in with Email + password (direct sign in, no 2FA).
    """
    try:
        data = request.get_json(silent=True) or {}
        raw_force_number = data.get("force_number")
        raw_email = data.get("email")
        raw_identifier = data.get("identifier")
        password = data.get("password")
        otp_code = (data.get("otp_code") or "").strip()
        totp_code = (data.get("totp_code") or "").strip()

        if not password:
            return jsonify({"error": "Password is required"}), 400

        is_force_number_attempt = False
        target_fn = None
        target_email = None

        if raw_force_number:
            is_force_number_attempt = True
            target_fn = str(raw_force_number).strip().upper()
        elif raw_identifier and "@" not in str(raw_identifier):
            is_force_number_attempt = True
            target_fn = str(raw_identifier).strip().upper()
        elif raw_email:
            target_email = str(raw_email).strip().lower()
        elif raw_identifier and "@" in str(raw_identifier):
            target_email = str(raw_identifier).strip().lower()
        else:
            return jsonify({"error": "Force Number or Email is required"}), 400

        user = None

        if is_force_number_attempt:
            fn_valid, fn_err = validate_force_number(target_fn)
            if not fn_valid:
                return jsonify({"error": fn_err}), 400

            user = User.query.filter(
                (User.force_number == target_fn) | (User.officer_id == target_fn)
            ).first()
        else:
            user = User.query.filter_by(email=target_email).first()

        def reject(event_type, custom_msg=None):
            write_audit_event(user.id if user else None, event_type)
            return jsonify({"error": custom_msg or "Invalid credentials"}), 401

        if user is None:
            return reject("LOGIN_FAILED")

        # Role enforcement for login method
        if is_force_number_attempt and user.role == "community":
            return jsonify({
                "error": "This account is registered as a community member. Please sign in using your email address."
            }), 400

        if not is_force_number_attempt and user.role in ("officer", "admin"):
            return jsonify({
                "error": "Police officers and administrators must log in with their Force Number (e.g. 123456X)."
            }), 400

        # Account lockout check
        if user.locked_until:
            locked_until = user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > datetime.now(timezone.utc):
                return reject("LOCKOUT", "Account temporarily locked due to multiple failed attempts. Please try again later.")

        # Verify password
        if not verify_password(user.password_hash, password):
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.session.commit()
            return reject("LOGIN_FAILED")

        # --- 2FA OTP for Officers & Admins ---
        if user.role in ("officer", "admin"):
            if not user.email:
                return jsonify({
                    "error": "No email address is associated with this Force Number. Please contact your system administrator."
                }), 500

            # If OTP code submitted, verify it
            if otp_code:
                is_valid, error_msg = otp_service.verify_otp(user.id, otp_code)
                if not is_valid:
                    write_audit_event(user.id, "OTP_FAILED")
                    return jsonify({"error": error_msg or "Invalid verification code"}), 401
                
                # OTP verified -> complete login
                return _complete_login(user)
            else:
                # Generate and send SMTP OTP to user's registered email
                success_msg, error_msg = otp_service.generate_otp(user.id)
                if error_msg:
                    # If email service fails, fall back to TOTP if user has enrolled TOTP
                    if user.totp_enabled:
                        if not totp_code or not verify_totp(user.totp_secret, totp_code):
                            return reject("MFA_FAILED")
                        return _complete_login(user)
                    else:
                        return jsonify({"error": f"Failed to send verification code: {error_msg}"}), 500

                write_audit_event(user.id, "OTP_SENT")
                masked = mask_email(user.email)
                return jsonify({
                    "requires_otp": True,
                    "message": f"A 6-digit verification code has been sent to {masked}",
                    "masked_email": masked,
                    "user_id": user.id,
                    "force_number": user.force_number or user.officer_id,
                    "role": user.role,
                }), 200

        # --- Community Members (Direct Sign-in, no 2FA) ---
        return _complete_login(user)

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


def _complete_login(user: User):
    """Complete the login process and issue tokens."""
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
