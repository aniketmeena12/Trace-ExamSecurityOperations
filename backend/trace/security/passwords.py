"""Password hashing with PBKDF2-HMAC-SHA256.

Self-contained (stdlib only) to avoid fragile native bcrypt builds. Format:
    pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
"""

import hashlib
import hmac
import os

# Iterations are configurable so tests can run fast; production keeps the strong
# default. The count used for each hash is stored in the hash string itself, so
# verification always uses the right value regardless of this setting.
ITERATIONS = int(os.environ.get("TRACE_PBKDF2_ITERS", "200000"))
SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)  # constant-time compare
    except (ValueError, AttributeError):
        return False
