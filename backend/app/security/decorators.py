from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import decode_token as fjwt_decode, get_jwt_identity
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = fjwt_decode(token)
        except ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        # flask-jwt-extended stores the identity in 'sub'
        sub = payload.get("sub")
        if not sub:
            return jsonify({"error": "Invalid token"}), 401

        # 'role' is stored as an additional claim
        role = payload.get("role")
        if not role:
            return jsonify({"error": "Invalid token"}), 401

        try:
            g.user_id = int(sub)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid token"}), 401

        g.role = role
        return f(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if g.role not in allowed_roles:
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
