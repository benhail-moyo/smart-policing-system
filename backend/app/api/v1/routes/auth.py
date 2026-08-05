from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app import db
from app.models.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or "community"

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    existing = db.session.query(User).filter_by(email=email).first()
    if existing:
        return jsonify({"error": "An account with that email already exists"}), 409

    user = User(
        name=name or email.split("@")[0],
        email=email,
        role=role if role in ("officer", "admin", "community") else "community",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "access_token": token,
        "user": user.to_dict(),
    }), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.session.query(User).filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "token": token,
        "access_token": token,
        "user": user.to_dict(),
    }), 200


@auth_bp.get("/me")
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if str(user_id).isdigit() else db.session.query(User).filter_by(email=str(user_id)).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200

