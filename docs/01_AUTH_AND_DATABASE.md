# Phase 1: Authentication & Database Foundation

> **Read `00_MASTER_IMPLEMENTATION_GUIDE.md` before starting this phase.**  
> **Estimated time:** 4–6 hours  
> **This phase is done when:** `flask db upgrade` runs without errors, JWT login returns a token, and role-based access denies unauthorized requests.

---

## Context for Claude

You are helping Benhail Moyo, a final-year Computer Science student at Midlands State University in Zimbabwe, build **Crime-Watch** — an AI-driven crime analytics and patrol optimization system for the Zimbabwe Republic Police.

The scaffold already exists at the paths shown in Section 3 of the Master Guide. Your job is to **complete and harden** the foundation — not rewrite what exists.

Current state of relevant files:
- `backend/app/__init__.py` → app factory exists, imports 4 blueprints
- `backend/app/config/settings.py` → Dev/Test/Prod config classes exist
- `backend/app/models/models.py` → User, Incident, Hotspot, PatrolRoute models exist with PostGIS columns
- `backend/app/api/v1/routes/auth.py` → register + login endpoints exist as stubs

---

## What Needs to Be Built in This Phase

### 1.1 Complete the User Model

The existing `User` model needs password hashing confirmed and the `check_password` method added as a model method (not just in the route).

**Add to `models.py`:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    # ... existing fields ...
    
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
```

### 1.2 Harden the Auth Routes

The existing `auth.py` has stubs. Complete them with:

**`POST /api/v1/auth/register`**
- Validate email format (use a simple regex or email-validator)
- Validate password minimum 8 characters
- Check for duplicate email → 409 Conflict
- Hash password via `user.set_password()`
- Return: `{ "id": int, "email": str, "role": str }`

**`POST /api/v1/auth/login`**
- Return: `{ "access_token": str, "role": str, "user_id": int }`
- On failure: `{ "error": "Invalid credentials" }` — always use this generic message (don't say "email not found" — that leaks user existence)

### 1.3 Role Enforcement Decorator

Create `backend/app/utils/auth_decorators.py`:

```python
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
        def my_endpoint():
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
```

Apply this decorator to hotspot analysis and patrol endpoints (officers only).

### 1.4 Database Migration Setup

```bash
cd backend/
flask db init          # Creates migrations/ folder (only run once)
flask db migrate -m "initial schema"
flask db upgrade
```

**Verify PostGIS is working:**
```python
# Run this in flask shell: flask shell
from app import db
result = db.session.execute(db.text("SELECT PostGIS_Version()")).scalar()
print(result)  # Should print e.g. "3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1"
```

### 1.5 Seed Script for Development

Create `backend/scripts/seed_dev_data.py`:

This script should:
1. Create 3 users: one admin, one officer, one community reporter
2. Create 20 synthetic incidents around Harare with PostGIS coordinates
3. Print the login credentials to stdout

**Harare coordinate ranges:**
```python
LAT_RANGE = (-17.95, -17.70)
LNG_RANGE = (30.95, 31.20)
```

Run with: `python backend/scripts/seed_dev_data.py`

---

## Acceptance Checklist

Test each of these manually before marking Phase 1 complete:

```bash
# 1. Database migrations apply cleanly
flask db upgrade
# Expected: no errors, tables exist in psql

# 2. Register a user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "officer@zrp.gov.zw", "password": "Test1234!", "role": "officer"}'
# Expected: 201 { "id": 1, "email": "officer@zrp.gov.zw", "role": "officer" }

# 3. Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "officer@zrp.gov.zw", "password": "Test1234!"}'
# Expected: 200 { "access_token": "eyJ...", "role": "officer" }

# 4. Duplicate email rejected
# Expected: 409 { "error": "Email already registered" }

# 5. Wrong password rejected
# Expected: 401 { "error": "Invalid credentials" }

# 6. Role enforcement
# Hit a patrol endpoint WITHOUT officer role → 403 Forbidden

# 7. Protected endpoint WITHOUT token
# Expected: 401 Unauthorized from JWT middleware
```

---

## Dissertation Notes for This Phase

**Chapter 3 (Methodology) material this generates:**
- Section on system security architecture (JWT stateless auth)
- Role-based access control table (already in Master Guide Section 6)
- Database schema diagram — generate this with: `\dt` in psql, then draw in draw.io

**Chapter 1 alignment:**
- Section 1.7 mentions "Flask-Login and 2FA" — note that for the dissertation proof-of-concept, JWT is used instead of session-based Flask-Login. This is a better engineering choice. Document the decision: JWT is stateless (no server-side session storage), making the system horizontally scalable. 2FA is identified as future work.

**Common examiner question:** "Why JWT instead of sessions?"  
Answer: Stateless authentication allows the API to be consumed by any client (mobile, web, third-party systems) without server-side session management. This aligns with REST principles.

---

## What You Learn in This Phase

- **Database migrations:** The professional way to evolve a schema. Never `db.create_all()` in production — that can't track changes.
- **Password hashing:** `generate_password_hash` uses PBKDF2-SHA256 with a random salt. Never store plain text passwords.
- **JWT flow:** Token issued at login → stored on client → sent on every request → verified by server → no session state needed.
- **Decorator pattern:** `@require_role` is a real-world Python pattern. You'll use this pattern everywhere in your career.
