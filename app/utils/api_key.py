"""API key check for the FastAPI endpoints (ISS-61)."""
import hmac
import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_ENV = "MANALOT_API_KEY"
API_KEY_HEADER = "X-API-Key"

_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


def require_api_key(key: str | None = Security(_header)) -> None:
    """Reject the request unless X-API-Key matches MANALOT_API_KEY.

    Fails closed: with no key configured, every request is refused.
    """
    expected = os.getenv(API_KEY_ENV)
    if not expected:
        raise HTTPException(status_code=503, detail="API key not configured.")
    if not key or not hmac.compare_digest(key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
