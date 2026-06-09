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

    # CORS origin for the Vite dev server (M4).
    FRONTEND_ORIGIN: str = os.environ.get("TRACE_FRONTEND_ORIGIN", "http://localhost:5173")

    def server_wrap_key(self) -> bytes:
        """32-byte key used to wrap a paper's AES key for post-release serving.

        Derived from SECRET_KEY so a raw DB dump (without the app secret) cannot
        decrypt a released paper.
        """
        return hashlib.sha256(self.SECRET_KEY.encode()).digest()


settings = Settings()
