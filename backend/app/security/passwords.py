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
