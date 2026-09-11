import pytest

from myhub.modules.administration.config import validate_canonical_url


def test_public_canonical_url_requires_https() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        validate_canonical_url("http://family.example.com")


def test_localhost_http_is_allowed_for_development() -> None:
    assert validate_canonical_url("http://localhost:8000/") == "http://localhost:8000"
