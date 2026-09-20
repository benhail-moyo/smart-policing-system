from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, VerificationError
from werkzeug.security import check_password_hash
import re
import difflib

ph = PasswordHasher()  # sane defaults: Argon2id, time_cost=3, memory_cost=64MB, parallelism=4

# Force Number format: exactly 6 digits followed by 1 uppercase letter (e.g., 123456X)
FORCE_NUMBER_PATTERN = re.compile(r"^\d{6}[A-Z]$")


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


def validate_force_number(force_number: str) -> tuple[bool, str]:
    """
    Validates that a Force Number matches the required 6-digit + 1-letter format (e.g. 123456X).
    Returns (is_valid, error_message).
    """
    if not force_number:
        return False, "Force Number is required for police officers and administrators."
    
    clean_fn = force_number.strip().upper()
    if not FORCE_NUMBER_PATTERN.match(clean_fn):
        return False, "Force Number must be exactly 6 digits followed by a capital letter (e.g. 123456X, 084512A)."
    
    return True, ""


def validate_password_strength(password: str, user_context: dict = None) -> tuple[bool, list[str]]:
    """
    Validates password strength according to organizational security policy:
    1. Must have at least 8 characters
    2. Must have at least one special character
    3. Must have at least one capital letter
    4. Must have at least one number
    5. Cannot be too similar to force number, name, or email

    Args:
        password: Plaintext password to evaluate.
        user_context: Optional dictionary containing 'name', 'email', and/or 'force_number'.

    Returns:
        tuple[bool, list[str]]: (is_valid, list_of_error_messages)
    """
    errors = []

    if not password:
        return False, ["Password is required."]

    # Rule 1: At least 8 characters
    if len(password) < 8:
        errors.append("Password must have at least 8 characters.")

    # Rule 2: At least one special character
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+[\]\\/`~;']", password):
        errors.append("Password must contain at least one special character (e.g. !@#$%^&*).")

    # Rule 3: At least one capital letter
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one capital letter (A-Z).")

    # Rule 4: At least one number
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number (0-9).")

    # Rule 5: Cannot be too similar to force number, name, or email
    if user_context and isinstance(user_context, dict):
        pw_lower = password.lower()
        candidate_tokens = set()

        # Extract tokens from name
        name = user_context.get("name") or ""
        for part in re.split(r"[\s._\-@]+", name):
            clean_part = part.strip().lower()
            if len(clean_part) >= 3:
                candidate_tokens.add(clean_part)

        # Extract tokens from email
        email = user_context.get("email") or ""
        if "@" in email:
            email_user = email.split("@")[0]
            for part in re.split(r"[\s._\-+]+", email_user):
                clean_part = part.strip().lower()
                if len(clean_part) >= 3:
                    candidate_tokens.add(clean_part)

        # Extract tokens from force number
        fn = user_context.get("force_number") or user_context.get("officer_id") or ""
        clean_fn = fn.strip().lower()
        if len(clean_fn) >= 3:
            candidate_tokens.add(clean_fn)
            digits_only = re.sub(r"\D", "", clean_fn)
            if len(digits_only) >= 4:
                candidate_tokens.add(digits_only)

        # Evaluate similarity against candidate tokens
        is_similar = False
        for token in candidate_tokens:
            # Substring check
            if token in pw_lower:
                is_similar = True
                break
            # Sequence similarity ratio
            ratio = difflib.SequenceMatcher(None, pw_lower, token).ratio()
            if ratio >= 0.7:
                is_similar = True
                break

        if is_similar:
            errors.append("Password cannot be too similar to your name, email, or force number.")

    return len(errors) == 0, errors
