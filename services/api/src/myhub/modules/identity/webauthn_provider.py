from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)


@dataclass(frozen=True, slots=True)
class WebAuthnConfig:
    rp_id: str
    rp_name: str
    expected_origin: str

    def __post_init__(self) -> None:
        rp_id = self.rp_id.strip().lower()
        origin = self.expected_origin.strip()
        if not rp_id or "://" in rp_id or "/" in rp_id:
            raise ValueError("rp_id must be a hostname without scheme or path")
        if not origin.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("expected_origin must be HTTPS except for local development")
        object.__setattr__(self, "rp_id", rp_id)
        object.__setattr__(self, "expected_origin", origin.rstrip("/"))


class WebAuthnProvider:
    """Thin internal port around py_webauthn.

    Challenge persistence/single-use semantics deliberately live outside this
    adapter. This class owns RP/origin/user-verification policy so individual
    route/application services cannot accidentally relax those checks.
    """

    def __init__(self, config: WebAuthnConfig) -> None:
        self.config = config

    def registration_options(
        self,
        *,
        user_id: bytes,
        user_name: str,
        user_display_name: str,
        challenge: bytes,
        exclude_credential_ids: Sequence[bytes] = (),
    ) -> Any:
        if not challenge:
            raise ValueError("challenge must not be empty")
        if not user_id:
            raise ValueError("user_id must not be empty")

        return generate_registration_options(
            rp_id=self.config.rp_id,
            rp_name=self.config.rp_name,
            user_id=user_id,
            user_name=user_name,
            user_display_name=user_display_name,
            challenge=challenge,
            exclude_credentials=[
                PublicKeyCredentialDescriptor(id=credential_id)
                for credential_id in exclude_credential_ids
            ],
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
        )

    def authentication_options(
        self,
        *,
        challenge: bytes,
        allow_credential_ids: Sequence[bytes] = (),
    ) -> Any:
        if not challenge:
            raise ValueError("challenge must not be empty")

        return generate_authentication_options(
            rp_id=self.config.rp_id,
            challenge=challenge,
            allow_credentials=[
                PublicKeyCredentialDescriptor(id=credential_id)
                for credential_id in allow_credential_ids
            ],
            user_verification=UserVerificationRequirement.REQUIRED,
        )

    def verify_registration(self, *, credential: Any, expected_challenge: bytes) -> Any:
        if not expected_challenge:
            raise ValueError("expected_challenge must not be empty")

        return verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=self.config.rp_id,
            expected_origin=self.config.expected_origin,
            require_user_verification=True,
        )

    def verify_authentication(
        self,
        *,
        credential: Any,
        expected_challenge: bytes,
        credential_public_key: bytes,
        credential_current_sign_count: int,
    ) -> Any:
        if not expected_challenge:
            raise ValueError("expected_challenge must not be empty")
        if not credential_public_key:
            raise ValueError("credential_public_key must not be empty")

        return verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=self.config.rp_id,
            expected_origin=self.config.expected_origin,
            credential_public_key=credential_public_key,
            credential_current_sign_count=credential_current_sign_count,
            require_user_verification=True,
        )
