from __future__ import annotations

import pytest
from webauthn.helpers.structs import UserVerificationRequirement

import myhub.modules.identity.webauthn_provider as provider_module
from myhub.modules.identity.webauthn_provider import WebAuthnConfig, WebAuthnProvider


def make_provider() -> WebAuthnProvider:
    return WebAuthnProvider(
        WebAuthnConfig(
            rp_id="family.example.com",
            rp_name="MyHub Family",
            expected_origin="https://family.example.com",
        )
    )


def test_config_rejects_url_as_rp_id() -> None:
    with pytest.raises(ValueError, match="rp_id"):
        WebAuthnConfig(
            rp_id="https://family.example.com",
            rp_name="MyHub",
            expected_origin="https://family.example.com",
        )


def test_config_requires_https_outside_local_development() -> None:
    with pytest.raises(ValueError, match="expected_origin"):
        WebAuthnConfig(
            rp_id="family.example.com",
            rp_name="MyHub",
            expected_origin="http://family.example.com",
        )


def test_registration_options_bind_rp_challenge_and_required_user_verification() -> None:
    provider = make_provider()
    options = provider.registration_options(
        user_id=b"user-123",
        user_name="alan",
        user_display_name="Alan",
        challenge=b"registration-challenge",
        exclude_credential_ids=[b"existing-credential"],
    )

    assert options.rp.id == "family.example.com"
    assert options.challenge == b"registration-challenge"
    assert options.user.id == b"user-123"
    assert options.authenticator_selection is not None
    assert options.authenticator_selection.user_verification is UserVerificationRequirement.REQUIRED
    assert [item.id for item in options.exclude_credentials] == [b"existing-credential"]


def test_authentication_options_require_user_verification() -> None:
    provider = make_provider()
    options = provider.authentication_options(
        challenge=b"authentication-challenge",
        allow_credential_ids=[b"credential-1"],
    )

    assert options.rp_id == "family.example.com"
    assert options.challenge == b"authentication-challenge"
    assert options.user_verification is UserVerificationRequirement.REQUIRED
    assert [item.id for item in options.allow_credentials] == [b"credential-1"]


def test_verify_registration_cannot_relax_rp_origin_or_user_verification(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_verify_registration_response(**kwargs):
        captured.update(kwargs)
        return "verified-registration"

    monkeypatch.setattr(provider_module, "verify_registration_response", fake_verify_registration_response)
    provider = make_provider()

    result = provider.verify_registration(
        credential={"id": "credential"},
        expected_challenge=b"challenge",
    )

    assert result == "verified-registration"
    assert captured["expected_rp_id"] == "family.example.com"
    assert captured["expected_origin"] == "https://family.example.com"
    assert captured["require_user_verification"] is True
    assert captured["expected_challenge"] == b"challenge"


def test_verify_authentication_cannot_relax_rp_origin_or_user_verification(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_verify_authentication_response(**kwargs):
        captured.update(kwargs)
        return "verified-authentication"

    monkeypatch.setattr(provider_module, "verify_authentication_response", fake_verify_authentication_response)
    provider = make_provider()

    result = provider.verify_authentication(
        credential={"id": "credential"},
        expected_challenge=b"challenge",
        credential_public_key=b"public-key",
        credential_current_sign_count=7,
    )

    assert result == "verified-authentication"
    assert captured["expected_rp_id"] == "family.example.com"
    assert captured["expected_origin"] == "https://family.example.com"
    assert captured["require_user_verification"] is True
    assert captured["credential_public_key"] == b"public-key"
    assert captured["credential_current_sign_count"] == 7
