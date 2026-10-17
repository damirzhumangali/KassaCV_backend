import os
import pytest
from fastapi import HTTPException
from app.auth import require_api_key


@pytest.mark.asyncio
async def test_require_api_key_valid(monkeypatch):
    monkeypatch.setenv("API_KEYS", "secret_key_1,secret_key_2")
    # Need to clear lru_cache of get_settings
    from app.config import get_settings
    get_settings.cache_clear()

    # Valid key should pass without error
    await require_api_key(x_api_key="secret_key_1")
    await require_api_key(x_api_key="secret_key_2")


@pytest.mark.asyncio
async def test_require_api_key_invalid(monkeypatch):
    monkeypatch.setenv("API_KEYS", "secret_key_1")
    from app.config import get_settings
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc_info:
        await require_api_key(x_api_key="wrong_key")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_api_key_missing(monkeypatch):
    monkeypatch.setenv("API_KEYS", "secret_key_1")
    from app.config import get_settings
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc_info:
        await require_api_key(x_api_key=None)
    assert exc_info.value.status_code == 401
