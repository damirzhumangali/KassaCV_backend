import hmac
from fastapi import Header, HTTPException

from app.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    keys = get_settings().api_keys
    valid = False
    supplied = x_api_key or ""
    # Always perform a constant-time comparison for each configured key.
    for key in keys:
        valid = hmac.compare_digest(supplied.encode(), key.encode()) or valid
    if not keys or not valid:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
