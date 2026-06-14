"""
[PHASE3] JWT-based authentication for Adam Prism.
Implements:
- User registration with bcrypt password hashing
- Login with JWT token issuance
- Token refresh
- Scope-based authorization (user, admin, service)

For local development, falls back to a single static API key
via the existing ADAM_API_KEY environment variable.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("adam_prism.auth")

# Try to import JWT libraries; fall back to simple HMAC if unavailable
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("PyJWT not available - using simple HMAC tokens")

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.warning("bcrypt not available - using PBKDF2 (slower)")

# Configuration
JWT_SECRET = os.environ.get("ADAM_JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = int(os.environ.get("ADAM_JWT_TTL", str(7 * 24 * 3600)))  # 7 days
JWT_REFRESH_TTL = int(os.environ.get("ADAM_JWT_REFRESH_TTL", str(30 * 24 * 3600)))


@dataclass
class TokenPayload:
    """[PHASE3] JWT token payload."""
    sub: str  # User ID
    email: str | None
    role: str  # user, admin, service
    scopes: list[str]
    exp: int  # Expiration timestamp
    iat: int  # Issued at

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or self.role == "admin"


def _fallback_hash_password(password: str) -> str:
    """[PHASE3] PBKDF2 fallback if bcrypt not available."""
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"pbkdf2$100000${salt}${h.hex()}"


def hash_password(password: str) -> str:
    """[PHASE3] Hash a password using bcrypt (or PBKDF2 fallback)."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return _fallback_hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """[PHASE3] Verify a password against its hash."""
    if not hashed:
        return False
    try:
        if hashed.startswith("pbkdf2$"):
            parts = hashed.split("$")
            if len(parts) != 4:
                return False
            _, iterations, salt, hash_hex = parts
            h = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
            )
            return hmac.compare_digest(h.hex(), hash_hex)
        if BCRYPT_AVAILABLE:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False
    return False


def create_access_token(
    user_id: str,
    email: str | None = None,
    role: str = "user",
    scopes: list[str] | None = None,
    ttl: int | None = None,
) -> str:
    """[PHASE3] Create a JWT access token."""
    if scopes is None:
        scopes = ["chat", "knowledge.read", "knowledge.write"]

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "scopes": scopes,
        "iat": int(time.time()),
        "exp": int(time.time()) + (ttl or JWT_TTL_SECONDS),
    }

    if JWT_AVAILABLE and JWT_SECRET:
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Fallback: simple HMAC token
    secret = JWT_SECRET or os.environ.get("ADAM_API_KEY", "adam-prism-change-me")
    import base64
    import json as _json
    header = base64.urlsafe_b64encode(_json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(_json.dumps(payload).encode()).rstrip(b"=").decode()
    signature = hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{body}.{signature}"


def create_refresh_token(user_id: str) -> str:
    """[PHASE3] Create a long-lived refresh token."""
    return create_access_token(
        user_id=user_id,
        role="refresh",
        scopes=["refresh"],
        ttl=JWT_REFRESH_TTL,
    )


def verify_token(token: str) -> Optional[TokenPayload]:
    """[PHASE3] Verify and decode a JWT token."""
    if not token:
        return None
    try:
        if JWT_AVAILABLE and JWT_SECRET:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        else:
            # Fallback HMAC verification
            import base64
            import json as _json
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header, body, signature = parts
            secret = JWT_SECRET or os.environ.get("ADAM_API_KEY", "adam-prism-change-me")
            expected_sig = hmac.new(
                secret.encode(), f"{header}.{body}".encode(), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return None
            # Decode body with padding
            padding = "=" * ((4 - len(body) % 4) % 4)
            payload = _json.loads(base64.urlsafe_b64decode(body + padding))

        if "exp" in payload and payload["exp"] < time.time():
            return None
        return TokenPayload(
            sub=payload.get("sub", ""),
            email=payload.get("email"),
            role=payload.get("role", "user"),
            scopes=payload.get("scopes", []),
            exp=payload.get("exp", 0),
            iat=payload.get("iat", 0),
        )
    except Exception as e:
        logger.debug(f"Token verification failed: {e}")
        return None


def generate_api_key() -> tuple[str, str]:
    """[PHASE3] Generate a new API key. Returns (plain_key, key_hash)."""
    plain = f"adam-{secrets.token_urlsafe(32)}"
    hashed = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    return plain, hashed


def hash_api_key(plain: str) -> str:
    """[PHASE3] Hash an API key for storage/lookup."""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()
