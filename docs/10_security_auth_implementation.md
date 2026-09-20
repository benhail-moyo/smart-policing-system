# Crime-Watch — Phase Prompt: Authentication, MFA & RBAC

**Project:** Crime-Watch (AI-driven crime analytics & patrol optimization — MSU dissertation)
**Phase:** Security Architecture — Authentication, Role-Based Access Control, Multi-Factor Authentication
**Corresponds to:** Dissertation Chapter 3, Section 3.6.4 (Security Architecture and Access Control)
**Stack constraint:** Flask (app-factory pattern) backend, PostgreSQL + PostGIS, Next.js/React frontend, JWT-based auth. Zero-cost tools only — no paid SMS gateways, no third-party identity providers (Auth0/Okta), no hardware keys.

---

## 0. Ground rules for the agent

- Do **not** invent a new backend framework, ORM, or auth pattern outside what's specified here — this must match the existing Flask app-factory + SQLAlchemy + PostGIS architecture already established in the project.
- Do **not** hand-roll cryptography (no custom hashing, no custom TOTP algorithm). Use the named libraries below — they are standard, audited, free, and citable in the dissertation (RFC 6238, OWASP guidance).
- Every protected endpoint must be enforced **server-side**. Anything done in React (hiding buttons, route guards) is a UX nicety only, never a security boundary. If you add a `@role_required` check anywhere, verify there is no code path that reaches the underlying logic without it.
- Ask before deviating from this spec (e.g. if `Flask-Limiter` conflicts with an existing dependency, stop and flag it — don't silently substitute something else).
- After each numbered step, run the relevant tests before moving to the next step.

---

## 1. Dependencies to add

```bash
pip install argon2-cffi pyjwt pyotp qrcode[pil] flask-limiter --break-system-packages
```

Add to `requirements.txt` (or `pyproject.toml`, whichever the project already uses):

```
argon2-cffi
PyJWT
pyotp
qrcode[pil]
Flask-Limiter
```

---

## 2. Database schema changes

Add/confirm the following columns on the existing `User` model (SQLAlchemy). If `User` doesn't exist yet, create it.

```python
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # 'community' | 'officer' | 'admin'

    # Identifiers — exactly one of these is populated per role convention,
    # but store both columns for flexibility.
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    officer_id = db.Column(db.String(50), unique=True, nullable=True, index=True)

    password_hash = db.Column(db.String(255), nullable=False)

    # MFA
    totp_secret = db.Column(db.String(64), nullable=True)       # base32 secret, set on enrolment
    totp_enabled = db.Column(db.Boolean, default=False, nullable=False)

    # Account lockout state (belt-and-suspenders alongside Flask-Limiter)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.CheckConstraint("role IN ('community','officer','admin')", name="valid_role"),
    )
```

Add a `RefreshToken` table so refresh tokens can be revoked server-side (a bare stateless JWT can't be revoked otherwise):

```python
class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token_hash = db.Column(db.String(128), nullable=False)  # store a hash, never the raw token
    issued_at = db.Column(db.DateTime, server_default=db.func.now())
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
```

Extend the **existing** PostGIS audit table (from the HITL workflow, Section 3.6.3 — do not create a second audit table) with an event-type row per auth event:
- `LOGIN_SUCCESS`, `LOGIN_FAILED`, `MFA_FAILED`, `LOCKOUT`, `ROLE_CHANGE`, `TOKEN_REFRESH`, `LOGOUT`

If the existing audit table's schema can't represent these (e.g. it's tightly coupled to route-override events only), add a generic `event_type` + `metadata JSONB` column rather than building a parallel table — flag this decision to the user if it requires a migration on an existing table.

Write an Alembic (or Flask-Migrate) migration for all of the above. Do not modify the database by hand.

---

## 3. Password hashing (Argon2id)

Create `security/passwords.py`:

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()  # sane defaults: Argon2id, time_cost=3, memory_cost=64MB, parallelism=4

def hash_password(plain: str) -> str:
    return ph.hash(plain)

def verify_password(stored_hash: str, plain: str) -> bool:
    try:
        return ph.verify(stored_hash, plain)
    except VerifyMismatchError:
        return False
```

- Never log the plaintext password, even at DEBUG level.
- Never store the plaintext password in any variable longer than necessary to hash it.

---

## 4. TOTP (MFA) enrolment and verification

Create `security/totp.py`:

```python
import pyotp
import qrcode
import io
import base64

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_provisioning_qr_base64(secret: str, account_name: str, issuer: str = "Crime-Watch") -> str:
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # allows ±30s clock drift
```

**Enrolment flow (Officer/Admin — mandatory):**
1. On account provisioning (admin creates an officer/admin account — see Section 6), generate a `totp_secret`, store it, but leave `totp_enabled = False`.
2. Serve the QR code (`get_provisioning_qr_base64`) to the user once, over an already-authenticated session, so they can scan it into an authenticator app.
3. Require the user to submit one valid TOTP code to confirm enrolment before flipping `totp_enabled = True`. Do not allow login without completing this step for officer/admin roles.

**Community accounts:** same flow, but optional — gate it behind a user-initiated "Enable 2FA" action in account settings rather than forcing it at registration.

---

## 5. JWT issuance and verification

Create `security/tokens.py`:

```python
import jwt
import datetime
import hashlib
import secrets
import os

SECRET_KEY = os.environ["JWT_SECRET_KEY"]  # fail loudly if unset — never hardcode a default
ACCESS_TOKEN_TTL = datetime.timedelta(minutes=15)
REFRESH_TOKEN_TTL = datetime.timedelta(days=7)

def issue_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + ACCESS_TOKEN_TTL,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def issue_refresh_token(user_id: int) -> str:
    raw = secrets.token_urlsafe(64)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": raw,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + REFRESH_TOKEN_TTL,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash  # caller stores token_hash in RefreshToken table, returns token to client

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # raises on expiry/tamper — let it propagate
```

- `JWT_SECRET_KEY` must come from an environment variable (`.env`, excluded from Git via `.gitignore`). Never commit it. Generate it once with `python -c "import secrets; print(secrets.token_hex(32))"`.
- Refresh tokens are single-use: on `/auth/refresh`, verify the incoming token's hash exists in `RefreshToken` and is not revoked, mark it revoked, and issue a brand-new refresh token (rotation) alongside the new access token. This is what makes a stolen-and-reused refresh token detectable — if a revoked token is presented again, treat it as a compromise signal and revoke *all* of that user's active refresh tokens.

---

## 6. Account provisioning rules (who can create which accounts)

This is a design decision, not just code — implement it exactly this way:

| Role | Who can create the account | Endpoint |
|---|---|---|
| `community` | Self-registration (public endpoint) | `POST /auth/register` |
| `officer` | Admin only | `POST /admin/users` (role-guarded) |
| `admin` | Admin only, or a one-time seeded bootstrap admin created via a CLI script (`flask create-admin`) — never via a public route | `POST /admin/users` (role-guarded) or CLI |

There must be **no public endpoint** that lets a client set `role=officer` or `role=admin` on registration. If you find or write a generic `POST /users` that accepts an arbitrary `role` field from the request body, that's a privilege-escalation bug — fix it by removing `role` from the self-registration payload entirely (it's hardcoded server-side to `community`).

Write the `flask create-admin` CLI command (Flask CLI custom command) as the only way to create the very first admin account on a fresh deployment.

---

## 7. RBAC decorator

Create `security/decorators.py`:

```python
from functools import wraps
from flask import request, jsonify, g
from .tokens import decode_token
import jwt as pyjwt

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = decode_token(token)
        except pyjwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        if payload.get("type") != "access":
            return jsonify({"error": "Invalid token type"}), 401
        g.user_id = int(payload["sub"])
        g.role = payload["role"]
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
```

Usage:

```python
@app.route("/patrol/routes", methods=["POST"])
@role_required("officer", "admin")
def generate_patrol_route():
    ...

@app.route("/admin/users", methods=["POST"])
@role_required("admin")
def create_user():
    ...

@app.route("/reports", methods=["POST"])
# no decorator — anonymous community submission is intentionally allowed
def submit_report():
    ...

@app.route("/reports/mine", methods=["GET"])
@login_required
def my_reports():
    # any authenticated role can view their own reports; filter by g.user_id
    ...
```

**Audit requirement:** grep the entire route table after this phase and confirm every route that touches officer/admin data, patrol routes, hotspot internals, or user management has a `role_required` decorator. Produce a checklist as output (route → required role → confirmed present Y/N).

---

## 8. Rate limiting & lockout

Configure `Flask-Limiter` in the app factory:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)
    limiter.init_app(app)
    ...
```

Apply to the login route specifically (tighter than global default):

```python
@app.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    ...
```

**Application-level lockout** (belt-and-suspenders alongside the IP-based limiter, since IP limits don't stop an attacker distributing requests across IPs against one account):
- On each failed password or TOTP check for a given account, increment `failed_login_count`.
- If `failed_login_count >= 5` within a 15-minute window, set `locked_until = now + 15 minutes` and reject further attempts on that account (even from a fresh IP) until `locked_until` passes.
- Reset `failed_login_count` to 0 on any successful login.
- Every lockout event must write to the audit log (`LOCKOUT`).

---

## 9. The login endpoint, end to end

```python
@app.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    identifier = data.get("identifier")  # email OR officer_id
    password = data.get("password")
    totp_code = data.get("totp_code")  # optional unless role requires it

    user = User.query.filter(
        (User.email == identifier) | (User.officer_id == identifier)
    ).first()

    # Uniform failure path — do not reveal whether identifier, password, or MFA failed
    def reject(event_type):
        write_audit_event(identifier, event_type)
        return jsonify({"error": "Invalid credentials"}), 401

    if user is None:
        return reject("LOGIN_FAILED")

    if user.locked_until and user.locked_until > datetime.utcnow():
        return reject("LOCKOUT")

    if not verify_password(user.password_hash, password):
        user.failed_login_count += 1
        if user.failed_login_count >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
        return reject("LOGIN_FAILED")

    if user.role in ("officer", "admin"):
        if not user.totp_enabled or not totp_code or not verify_totp(user.totp_secret, totp_code):
            return reject("MFA_FAILED")
    elif user.totp_enabled:  # community user who opted into 2FA
        if not totp_code or not verify_totp(user.totp_secret, totp_code):
            return reject("MFA_FAILED")

    user.failed_login_count = 0
    user.locked_until = None
    db.session.commit()

    access_token = issue_access_token(user.id, user.role)
    refresh_token, refresh_hash = issue_refresh_token(user.id)
    db.session.add(RefreshToken(
        user_id=user.id, token_hash=refresh_hash,
        expires_at=datetime.utcnow() + REFRESH_TOKEN_TTL
    ))
    db.session.commit()

    write_audit_event(identifier, "LOGIN_SUCCESS")
    return jsonify({"access_token": access_token, "refresh_token": refresh_token, "role": user.role})
```

Also implement, following the same patterns:
- `POST /auth/refresh` — rotate refresh token, issue new access token
- `POST /auth/logout` — revoke the presented refresh token
- `POST /auth/register` — community self-registration only, `role` hardcoded to `community`, no TOTP required
- `POST /auth/mfa/enroll` — authenticated route, generates secret + QR (Section 4)
- `POST /auth/mfa/confirm` — authenticated route, verifies first TOTP code, flips `totp_enabled`

---

## 10. Frontend (Next.js/React) integration notes

- Store the access token in memory (React state/context), **not** `localStorage` (XSS-exploitable). Store the refresh token in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie if the Flask backend and Next.js frontend share a domain/subdomain; if fully cross-origin, discuss the trade-off with the user before choosing `localStorage` as a fallback — flag this as a decision point, don't silently pick one.
- Attach the access token as `Authorization: Bearer <token>` on every API call from the Next.js API-route proxy layer (per the existing thin-proxy architecture — token handling logic still lives in Python/Flask, the Next.js route just forwards the header).
- On a 401 with an expired access token, attempt one silent `/auth/refresh` call, then retry the original request once. On a second 401, force logout.
- Role-conditional UI (hiding admin nav items etc.) is fine for UX but must be clearly commented in the code as **not a security control** — the actual enforcement is server-side.

---

## 11. Testing checklist (must pass before this phase is marked done)

- [ ] Password is never present in logs, error responses, or Git history
- [ ] Argon2 hash verified for correct/incorrect password on a real account
- [ ] Officer/admin login rejected without a valid TOTP code, even with correct password
- [ ] Community login succeeds without TOTP unless the user has opted in
- [ ] 6 rapid failed logins on one account trigger lockout; 6th+ attempt rejected even with correct password
- [ ] Locked account audit-logs a `LOCKOUT` event
- [ ] Expired access token is rejected by `login_required`
- [ ] Refresh token rotation: using a refresh token twice fails the second time
- [ ] `role_required("admin")` route rejects a valid officer token with 403
- [ ] No public route accepts a client-supplied `role` field
- [ ] `flask create-admin` is the only way to create the first admin
- [ ] All auth events appear in the audit table with correct `event_type`
- [ ] Full route audit checklist (Section 7) completed with no gaps

---

## 12. Deliverable for the dissertation

Once implemented, produce a short results note (for Chapter 4) documenting:
1. Screenshot or log excerpt of a successful TOTP enrolment (QR + confirmation)
2. Screenshot or log excerpt of a rejected login due to lockout
3. The completed route-audit checklist from Section 7 (route → role → enforced Y/N) — this table doubles as evidence of systematic access-control verification, which examiners look for
4. Any deviations made from this spec during implementation, with justification (e.g., if `Flask-Limiter`'s in-memory store was used for the prototype instead of Redis — note this as a known limitation for production deployment, not silently omit it)
