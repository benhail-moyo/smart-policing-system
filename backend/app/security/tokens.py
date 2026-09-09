"""
Token issuance and decoding — Crime-Watch
=========================================
Uses flask-jwt-extended so that tokens are compatible with
    @jwt_required / @jwt_required(optional=True)
as well as the custom login_required decorator in decorators.py.
"""
import datetime
import hashlib
import secrets
import os

from dotenv import load_dotenv
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token as _fjwt_decode

load_dotenv()

ACCESS_TOKEN_TTL = datetime.timedelta(minutes=60)
REFRESH_TOKEN_TTL = datetime.timedelta(days=7)


def issue_access_token(user_id: int, role: str) -> str:
    """
    Issue a flask-jwt-extended access token.

    The identity is the user_id (int) and 'role' is added as an
    additional claim so decorators can read it without a DB lookup.
    """
    return create_access_token(
        identity=str(user_id),
        additional_claims={"role": role, "type": "access"},
        expires_delta=ACCESS_TOKEN_TTL,
    )


def issue_refresh_token(user_id: int):
    """
    Issue a flask-jwt-extended refresh token.

    Returns (token_str, sha256_hash) — the hash is stored in the DB,
    never the raw token.
    """
    token = create_refresh_token(
        identity=str(user_id),
        additional_claims={"type": "refresh"},
        expires_delta=REFRESH_TOKEN_TTL,
    )
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


def decode_token(token: str) -> dict:
    """
    Decode and validate a flask-jwt-extended token.

    Returns the claims payload dict.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure
    (flask-jwt-extended wraps these as PyJWT exceptions, so the existing
    decorators.py exception handling continues to work).
    """
    decoded = _fjwt_decode(token)
    # flask-jwt-extended nests claims under 'sub' (identity) + root level
    # Normalise into the flat dict our decorators expect:
    payload = dict(decoded)
    if "sub" in payload and "sub" not in payload:
        payload["sub"] = decoded["sub"]
    return payload


def refresh_token_hash(token: str) -> str:
    """Generate SHA256 hash of refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()
