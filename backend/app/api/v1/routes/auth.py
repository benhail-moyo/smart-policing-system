from flask import Blueprint, request
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    return {
        "message": "Registration scaffolded",
        "user": {"email": data.get("email")},
    }, 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    identity = data.get("email") or "development-user"
    return {"access_token": create_access_token(identity=identity)}, 200
