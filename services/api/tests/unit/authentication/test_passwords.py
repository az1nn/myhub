from __future__ import annotations

import pytest

from myhub.modules.identity.passwords import LoginNameError, PasswordService, normalize_login_name


def test_login_name_is_nfkc_trimmed_and_casefolded() -> None:
    assert normalize_login_name("  Ａlan  ") == "alan"


def test_login_name_rejects_internal_whitespace() -> None:
    with pytest.raises(LoginNameError, match="disallowed"):
        normalize_login_name("alan sa")


def test_login_name_rejects_too_short_value() -> None:
    with pytest.raises(LoginNameError, match="length"):
        normalize_login_name("ab")


def test_password_hash_uses_argon2id_owasp_floor() -> None:
    service = PasswordService()
    encoded = service.hash("correct horse battery staple")

    assert encoded.startswith("$argon2id$")
    assert "m=19456,t=2,p=1" in encoded
    assert service.verify(encoded, "correct horse battery staple") is True
    assert service.verify(encoded, "wrong password") is False
    assert service.needs_rehash(encoded) is False


def test_password_hash_rejects_empty_password() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        PasswordService().hash("")
