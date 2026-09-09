from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.models import User
from app import db


def require_role(*roles):
    """
    Usage:
        @jwt_required()
        @require_role('officer', 'admin')
        def endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = get_jwt_identity()
            user = db.session.get(User, user_id)
            if not user or user.role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# Legacy decorator for compatibility with existing code.
# New code should use app.security.decorators.role_required instead.
def legacy_require_role(*roles):
    """
    Legacy decorator for Flask-JWT-Extended compatibility.
    New endpoints should use app.security.decorators.role_required instead.
    """
    return require_role(*roles)
