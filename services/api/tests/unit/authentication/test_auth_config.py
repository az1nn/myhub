from __future__ import annotations

import pytest
from pydantic import ValidationError

from myhub.modules.administration.config import Settings


BASE = {
    "database_url": "sqlite+pysqlite:///:memory:",
    "bootstrap_token": "test-bootstrap-token-that-is-long-enough-12345",
}


def test_argon2_memory_cannot_drop_below_security_floor() -> None:
    with pytest.raises(ValidationError, match="19456"):
        Settings(**BASE, password_argon2_memory_kib=19_455)


def test_argon2_time_cost_cannot_drop_below_security_floor() -> None:
    with pytest.raises(ValidationError, match="at least 2"):
        Settings(**BASE, password_argon2_time_cost=1)


def test_challenge_ttl_is_bounded() -> None:
    with pytest.raises(ValidationError, match="between 30 and 900"):
        Settings(**BASE, auth_challenge_ttl_seconds=901)


def test_session_ttl_is_finite() -> None:
    with pytest.raises(ValidationError, match="365 days"):
        Settings(**BASE, auth_session_ttl_seconds=366 * 24 * 60 * 60)
