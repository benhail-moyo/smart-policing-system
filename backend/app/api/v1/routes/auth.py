from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import re

from app import db
from app.models.models import User

auth_bp = Blueprint("auth", __name__)


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "community")

    if not email or not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email"}), 400
    if not password or len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if db.session.query(User).filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"id": user.id, "email": user.email, "role": user.role}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Invalid credentials"}), 401

    user = db.session.query(User).filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({"access_token": access_token, "role": user.role, "user_id": user.id}), 200
