from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, VerificationError
from werkzeug.security import check_password_hash

ph = PasswordHasher()  # sane defaults: Argon2id, time_cost=3, memory_cost=64MB, parallelism=4

def hash_password(plain: str) -> str:
    return ph.hash(plain)

def verify_password(stored_hash: str, plain: str) -> bool:
    if not stored_hash or not plain:
        return False
    try:
        if stored_hash.startswith("scrypt:") or stored_hash.startswith("pbkdf2:"):
            return check_password_hash(stored_hash, plain)
        return ph.verify(stored_hash, plain)
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        # Fallback to werkzeug check in case format wasn't recognized by prefix
        try:
            return check_password_hash(stored_hash, plain)
        except Exception:
            return False
    except Exception:
        return False
