"""Runtime configuration for the Trace backend.

All secrets and tunables come from environment variables so nothing sensitive is
hard-coded. Defaults are dev-only and clearly insecure on purpose.
"""

import hashlib
import os


class Settings:
    # Signs JWTs AND derives the server wrapping key for released paper keys.
    SECRET_KEY: str = os.environ.get(
        "TRACE_SECRET_KEY", "dev-insecure-secret-change-me-in-production"
    )
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_TTL_MIN: int = int(os.environ.get("TRACE_TOKEN_TTL_MIN", "720"))

    DB_URL: str = os.environ.get("TRACE_DB_URL", "sqlite:///./trace.db")

    # CORS origins. Accepts a comma-separated list so deploy previews, a custom
    # domain, and the local dev server can coexist:
    #   TRACE_FRONTEND_ORIGIN=https://app.example.com,http://localhost:5173
    # Each entry is stripped and has any trailing slash removed — browsers send
    # Origin as scheme://host[:port] with no path, so a stray slash or a space
    # picked up from a copy-paste would otherwise match nothing at all and fail
    # every request with an opaque CORS error.
    FRONTEND_ORIGIN: str = os.environ.get("TRACE_FRONTEND_ORIGIN", "http://localhost:5173")

    @property
    def frontend_origins(self) -> list[str]:
        origins = [o.strip().rstrip("/") for o in self.FRONTEND_ORIGIN.split(",")]
        origins = [o for o in origins if o]
        return origins or ["http://localhost:5173"]

    def server_wrap_key(self) -> bytes:
        """32-byte key used to wrap a paper's AES key for post-release serving.

        Derived from SECRET_KEY so a raw DB dump (without the app secret) cannot
        decrypt a released paper.
        """
        return hashlib.sha256(self.SECRET_KEY.encode()).digest()

    def question_bank_key(self) -> bytes:
        """32-byte key encrypting individual questions in the dynamic bank.

        Domain-separated from server_wrap_key so the two keys are independent.
        Question bodies are AES-256-GCM ciphertext at rest; a raw DB dump cannot
        read them without this app secret. This protects the *bank contents*; the
        unpredictability of which questions reach a given candidate is enforced
        separately, by deriving the per-candidate selection from the exam key —
        which only exists after the Shamir quorum and the time gate both open.
        """
        return hashlib.sha256(self.SECRET_KEY.encode() + b"|question-bank").digest()


settings = Settings()
