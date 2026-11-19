"""Password hashing.

bcrypt stores a salted hash. The original password cannot be recovered
from the database, including by an administrator.
"""

import bcrypt

def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    # bcrypt only uses the first 72 bytes. Reject longer passwords explicitly.
    if len(password_bytes) > 72:
        raise ValueError("Password is too long.")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
