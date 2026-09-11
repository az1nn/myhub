from __future__ import annotations

import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from webauthn import base64url_to_bytes, options_to_json
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import CredentialDeviceType

from myhub.domain.bootstrap import BootstrapState
from myhub.infrastructure.db.models import (
    InitialOwnerEnrollmentModel,
    InstanceBootstrapModel,
    PasskeyCredentialModel,
    PasswordCredentialModel,
    UserModel,
)
from myhub.modules.administration.bootstrap_repository import BOOTSTRAP_ROW_ID
from myhub.modules.administration.config import Settings
from myhub.modules.identity.challenges import ChallengeError, ChallengePurpose, ChallengeService
from myhub.modules.identity.passwords import Argon2idPolicy, LoginNameError, PasswordService, normalize_login_name
from myhub.modules.identity.sessions import AuthenticatedSession, IssuedSession, SessionCredentialError, SessionService
from myhub.modules.identity.throttle import AuthenticationThrottled, LoginThrottleService, ThrottlePolicy
from myhub.modules.identity.webauthn_provider import WebAuthnConfig, WebAuthnProvider


class AuthError(RuntimeError):
    code = "AUTH_ERROR"
    status_code = 400
    public_message = "authentication request failed"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.public_message)


class InvalidCredentials(AuthError):
    code = "AUTH_INVALID_CREDENTIALS"
    status_code = 401
    public_message = "invalid credentials"


class InitialEnrollmentUnauthorized(AuthError):
    code = "AUTH_INITIAL_ENROLLMENT_UNAUTHORIZED"
    status_code = 401
    public_message = "initial enrollment is not authorized"


class InitialEnrollmentClosed(AuthError):
    code = "AUTH_INITIAL_ENROLLMENT_CLOSED"
    status_code = 409
    public_message = "initial Owner enrollment is closed"


class CredentialConflict(AuthError):
    code = "AUTH_CREDENTIAL_CONFLICT"
    status_code = 409
    public_message = "credential conflicts with existing authentication state"


class AuthenticationUnavailable(AuthError):
    code = "AUTH_UNAVAILABLE"
    status_code = 409
    public_message = "authentication is not available for this instance state"


class TooManyAuthenticationAttempts(AuthError):
    code = "AUTH_THROTTLED"
    status_code = 429
    public_message = "authentication temporarily throttled"


@dataclass(frozen=True, slots=True)
class CeremonyOptions:
    challenge_token: str
    public_key: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SessionResult:
    user_id: str
    session_id: str
    bearer_token: str
    expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    def __init__(self, *, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.challenges = ChallengeService(
            session,
            ttl_seconds=settings.auth_challenge_ttl_seconds,
        )
        self.sessions = SessionService(
            session,
            ttl_seconds=settings.auth_session_ttl_seconds,
        )
        self.passwords = PasswordService(
            Argon2idPolicy(
                memory_cost_kib=settings.password_argon2_memory_kib,
                time_cost=settings.password_argon2_time_cost,
                parallelism=settings.password_argon2_parallelism,
            )
        )
        self.throttle = LoginThrottleService(
            session,
            ThrottlePolicy(
                max_failures=settings.auth_login_max_failures,
                window_seconds=settings.auth_login_window_seconds,
                block_seconds=settings.auth_login_block_seconds,
            ),
        )

    # ----- Initial Owner bridge -------------------------------------------------

    def initial_owner_passkey_options(self, *, bootstrap_token: str) -> CeremonyOptions:
        with self.session.begin():
            instance, owner, _enrollment = self._initial_owner_context(bootstrap_token)
            issued = self.challenges.issue(
                purpose=ChallengePurpose.REGISTRATION,
                user_id=owner.id,
            )
            existing_ids = self.session.scalars(
                select(PasskeyCredentialModel.credential_id).where(
                    PasskeyCredentialModel.user_id == owner.id,
                    PasskeyCredentialModel.revoked_at.is_(None),
                )
            ).all()
            options = self._provider(instance).registration_options(
                user_id=owner.id.encode("utf-8"),
                user_name=owner.id,
                user_display_name=owner.display_name,
                challenge=issued.raw,
                exclude_credential_ids=existing_ids,
            )
            return CeremonyOptions(
                challenge_token=issued.token,
                public_key=json.loads(options_to_json(options)),
            )

    def verify_initial_owner_passkey(
        self,
        *,
        bootstrap_token: str,
        challenge_token: str,
        credential: dict[str, Any],
    ) -> SessionResult:
        """Verify the initial Owner ceremony without making challenge replayable.

        Challenge consumption commits before WebAuthn verification. A malformed or
        invalid assertion therefore burns the challenge rather than rolling its
        consumed marker back with the failed credential transaction.
        """

        try:
            with self.session.begin():
                instance, owner, _enrollment = self._initial_owner_context(bootstrap_token)
                owner_id = owner.id
                provider = self._provider(instance)

            expected_challenge = self._consume_challenge_committed(
                token=challenge_token,
                purpose=ChallengePurpose.REGISTRATION,
                user_id=owner_id,
            )
            verification = provider.verify_registration(
                credential=credential,
                expected_challenge=expected_challenge,
            )

            with self.session.begin():
                _instance, owner, enrollment = self._initial_owner_context(bootstrap_token)
                if owner.id != owner_id:
                    raise AuthenticationUnavailable()

                transports = credential.get("response", {}).get("transports")
                self.session.add(
                    PasskeyCredentialModel(
                        id=str(uuid4()),
                        user_id=owner.id,
                        credential_id=verification.credential_id,
                        credential_public_key=verification.credential_public_key,
                        sign_count=verification.sign_count,
                        transports_json=json.dumps(transports) if transports else None,
                        backup_eligible=(
                            verification.credential_device_type == CredentialDeviceType.MULTI_DEVICE
                        ),
                        backup_state=verification.credential_backed_up,
                    )
                )
                self._complete_initial_enrollment(enrollment)
                issued_session = self.sessions.issue(user_id=owner.id)
                return self._session_result(issued_session)
        except (ChallengeError, InvalidRegistrationResponse, ValueError) as exc:
            self._rollback_if_needed()
            raise InvalidCredentials() from exc
        except IntegrityError as exc:
            self._rollback_if_needed()
            raise CredentialConflict() from exc

    def initial_owner_password_enroll(
        self,
        *,
        bootstrap_token: str,
        login_name: str,
        password: str,
    ) -> SessionResult:
        try:
            canonical_login = normalize_login_name(login_name)
            encoded_hash = self.passwords.hash(password)
            with self.session.begin():
                _instance, owner, enrollment = self._initial_owner_context(bootstrap_token)
                self._upsert_password(owner.id, canonical_login, encoded_hash)
                self._complete_initial_enrollment(enrollment)
                issued_session = self.sessions.issue(user_id=owner.id)
                return self._session_result(issued_session)
        except (LoginNameError, ValueError) as exc:
            self._rollback_if_needed()
            raise InvalidCredentials() from exc
        except IntegrityError as exc:
            self._rollback_if_needed()
            raise CredentialConflict() from exc

    # ----- Passkey authentication ---------------------------------------------

    def passkey_authentication_options(self, *, client_key: str) -> CeremonyOptions:
        try:
            with self.session.begin():
                self.throttle.check(f"ip:{client_key}")
                instance = self._ready_instance()
                issued = self.challenges.issue(
                    purpose=ChallengePurpose.AUTHENTICATION,
                    user_id=None,
                )
                options = self._provider(instance).authentication_options(
                    challenge=issued.raw,
                )
                return CeremonyOptions(
                    challenge_token=issued.token,
                    public_key=json.loads(options_to_json(options)),
                )
        except AuthenticationThrottled as exc:
            self._rollback_if_needed()
            raise TooManyAuthenticationAttempts() from exc

    def verify_passkey_authentication(
        self,
        *,
        challenge_token: str,
        credential: dict[str, Any],
        client_key: str,
    ) -> SessionResult:
        throttle_key = f"ip:{client_key}"

        try:
            with self.session.begin():
                self.throttle.check(throttle_key)
        except AuthenticationThrottled as exc:
            self._rollback_if_needed()
            raise TooManyAuthenticationAttempts() from exc

        try:
            expected_challenge = self._consume_challenge_committed(
                token=challenge_token,
                purpose=ChallengePurpose.AUTHENTICATION,
                user_id=None,
            )
            credential_id = self._credential_id(credential)

            with self.session.begin():
                stored = self.session.scalar(
                    select(PasskeyCredentialModel)
                    .where(
                        PasskeyCredentialModel.credential_id == credential_id,
                        PasskeyCredentialModel.revoked_at.is_(None),
                    )
                    .with_for_update()
                )
                if stored is None:
                    raise InvalidCredentials()

                self._verify_user_handle(credential, stored.user_id)
                verification = self._provider(self._ready_instance()).verify_authentication(
                    credential=credential,
                    expected_challenge=expected_challenge,
                    credential_public_key=stored.credential_public_key,
                    credential_current_sign_count=stored.sign_count,
                )
                backup_eligible = verification.credential_device_type == CredentialDeviceType.MULTI_DEVICE
                if backup_eligible != stored.backup_eligible:
                    raise InvalidCredentials()

                stored.sign_count = verification.new_sign_count
                stored.backup_state = verification.credential_backed_up
                stored.last_used_at = _utcnow()
                self.throttle.record_success(throttle_key)
                issued_session = self.sessions.issue(user_id=stored.user_id)
                return self._session_result(issued_session)
        except InvalidCredentials:
            self._rollback_if_needed()
            self._record_failure_committed(throttle_key)
            raise
        except (ChallengeError, InvalidAuthenticationResponse, KeyError, ValueError) as exc:
            self._rollback_if_needed()
            self._record_failure_committed(throttle_key)
            raise InvalidCredentials() from exc

    # ----- Password fallback ---------------------------------------------------

    def enroll_password_for_session(
        self,
        *,
        bearer_token: str,
        login_name: str,
        password: str,
    ) -> None:
        try:
            canonical_login = normalize_login_name(login_name)
            encoded_hash = self.passwords.hash(password)
            with self.session.begin():
                authenticated = self.sessions.authenticate(bearer_token)
                self._upsert_password(authenticated.user_id, canonical_login, encoded_hash)
        except SessionCredentialError as exc:
            self._rollback_if_needed()
            raise InvalidCredentials() from exc
        except (LoginNameError, ValueError) as exc:
            self._rollback_if_needed()
            raise InvalidCredentials() from exc
        except IntegrityError as exc:
            self._rollback_if_needed()
            raise CredentialConflict() from exc

    def password_login(
        self,
        *,
        login_name: str,
        password: str,
        client_key: str,
    ) -> SessionResult:
        try:
            canonical_login = normalize_login_name(login_name)
        except LoginNameError:
            canonical_login = "invalid-login"

        keys = (f"ip:{client_key}", f"login:{canonical_login}")
        try:
            with self.session.begin():
                self.throttle.check(*keys)
        except AuthenticationThrottled as exc:
            self._rollback_if_needed()
            raise TooManyAuthenticationAttempts() from exc

        try:
            with self.session.begin():
                credential = self.session.scalar(
                    select(PasswordCredentialModel)
                    .where(
                        PasswordCredentialModel.login_name == canonical_login,
                        PasswordCredentialModel.revoked_at.is_(None),
                    )
                    .with_for_update()
                )
                if credential is None or not self.passwords.verify(credential.password_hash, password):
                    raise InvalidCredentials()

                if self.passwords.needs_rehash(credential.password_hash):
                    credential.password_hash = self.passwords.hash(password)
                self.throttle.record_success(*keys)
                issued_session = self.sessions.issue(user_id=credential.user_id)
                return self._session_result(issued_session)
        except InvalidCredentials:
            self._rollback_if_needed()
            self._record_failure_committed(*keys)
            raise

    def authenticate_session(self, bearer_token: str) -> AuthenticatedSession:
        try:
            with self.session.begin():
                return self.sessions.authenticate(bearer_token)
        except SessionCredentialError as exc:
            self._rollback_if_needed()
            raise InvalidCredentials() from exc

    def logout(self, bearer_token: str) -> None:
        with self.session.begin():
            self.sessions.revoke(bearer_token)

    # ----- Internal helpers ----------------------------------------------------

    def _consume_challenge_committed(
        self,
        *,
        token: str,
        purpose: ChallengePurpose,
        user_id: str | None,
    ) -> bytes:
        with self.session.begin():
            return self.challenges.consume(
                token=token,
                purpose=purpose,
                user_id=user_id,
            )

    def _record_failure_committed(self, *keys: str) -> None:
        self._rollback_if_needed()
        try:
            with self.session.begin():
                self.throttle.record_failure(*keys)
        except IntegrityError:
            # A concurrent first failure may race on the digest row. Retrying once
            # after rollback preserves the failure signal without requiring Redis.
            self.session.rollback()
            with self.session.begin():
                self.throttle.record_failure(*keys)

    def _rollback_if_needed(self) -> None:
        if self.session.in_transaction():
            self.session.rollback()

    def _ready_instance(self, *, lock: bool = False) -> InstanceBootstrapModel:
        statement = select(InstanceBootstrapModel).where(InstanceBootstrapModel.id == BOOTSTRAP_ROW_ID)
        if lock:
            statement = statement.with_for_update()
        instance = self.session.scalar(statement)
        if (
            instance is None
            or instance.state != BootstrapState.READY.value
            or not instance.owner_user_id
            or not instance.canonical_url
        ):
            raise AuthenticationUnavailable()
        return instance

    def _initial_owner_context(
        self,
        bootstrap_token: str,
    ) -> tuple[InstanceBootstrapModel, UserModel, InitialOwnerEnrollmentModel]:
        expected_token = self.settings.bootstrap_token.get_secret_value()
        if not hmac.compare_digest(bootstrap_token, expected_token):
            raise InitialEnrollmentUnauthorized()

        instance = self._ready_instance(lock=True)
        owner = self.session.get(UserModel, instance.owner_user_id)
        if owner is None:
            raise AuthenticationUnavailable()

        enrollment = self.session.scalar(
            select(InitialOwnerEnrollmentModel)
            .where(InitialOwnerEnrollmentModel.id == 1)
            .with_for_update()
        )
        if enrollment is None:
            enrollment = InitialOwnerEnrollmentModel(
                id=1,
                user_id=owner.id,
                status="PENDING",
            )
            self.session.add(enrollment)
            self.session.flush()
        if enrollment.user_id != owner.id:
            raise AuthenticationUnavailable()
        if enrollment.status == "COMPLETED" or enrollment.completed_at is not None:
            raise InitialEnrollmentClosed()
        return instance, owner, enrollment

    @staticmethod
    def _complete_initial_enrollment(enrollment: InitialOwnerEnrollmentModel) -> None:
        enrollment.status = "COMPLETED"
        enrollment.completed_at = _utcnow()

    def _provider(self, instance: InstanceBootstrapModel) -> WebAuthnProvider:
        parsed = urlparse(instance.canonical_url or "")
        if not parsed.hostname or not parsed.scheme or not parsed.netloc:
            raise AuthenticationUnavailable()
        return WebAuthnProvider(
            WebAuthnConfig(
                rp_id=parsed.hostname,
                rp_name="MyHub",
                expected_origin=f"{parsed.scheme}://{parsed.netloc}",
            )
        )

    def _upsert_password(self, user_id: str, login_name: str, encoded_hash: str) -> None:
        conflict = self.session.scalar(
            select(PasswordCredentialModel).where(
                PasswordCredentialModel.login_name == login_name,
                PasswordCredentialModel.user_id != user_id,
                PasswordCredentialModel.revoked_at.is_(None),
            )
        )
        if conflict is not None:
            raise CredentialConflict()

        credential = self.session.scalar(
            select(PasswordCredentialModel)
            .where(PasswordCredentialModel.user_id == user_id)
            .with_for_update()
        )
        if credential is None:
            self.session.add(
                PasswordCredentialModel(
                    id=str(uuid4()),
                    user_id=user_id,
                    login_name=login_name,
                    password_hash=encoded_hash,
                )
            )
            self.session.flush()
            return

        credential.login_name = login_name
        credential.password_hash = encoded_hash
        credential.revoked_at = None
        credential.updated_at = _utcnow()
        self.session.flush()

    @staticmethod
    def _credential_id(credential: dict[str, Any]) -> bytes:
        value = credential.get("id")
        if not isinstance(value, str) or not value:
            raise InvalidCredentials()
        return base64url_to_bytes(value)

    @staticmethod
    def _verify_user_handle(credential: dict[str, Any], expected_user_id: str) -> None:
        response = credential.get("response")
        if not isinstance(response, dict):
            raise InvalidCredentials()
        user_handle = response.get("userHandle")
        if user_handle is None:
            return
        if not isinstance(user_handle, str) or base64url_to_bytes(user_handle) != expected_user_id.encode("utf-8"):
            raise InvalidCredentials()

    @staticmethod
    def _session_result(session: IssuedSession) -> SessionResult:
        return SessionResult(
            user_id=session.user_id,
            session_id=session.id,
            bearer_token=session.bearer_token,
            expires_at=session.expires_at,
        )
