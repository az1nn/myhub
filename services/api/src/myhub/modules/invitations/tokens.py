from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import InvitationModel


class InvitationTokenError(RuntimeError):
    """Raised when an invitation bearer token cannot be resolved safely."""


@dataclass(frozen=True, slots=True)
class IssuedInvitationToken:
    invitation_id: str
    raw_token: str
    token_hash: str


class InvitationTokenService:
    SECRET_BYTES = 32

    def __init__(self, session: Session) -> None:
        self.session = session

    @classmethod
    def issue(cls) -> IssuedInvitationToken:
        invitation_id = str(uuid4())
        secret = secrets.token_bytes(cls.SECRET_BYTES)
        encoded_secret = cls._encode_secret(secret)
        return IssuedInvitationToken(
            invitation_id=invitation_id,
            raw_token=f"{invitation_id}.{encoded_secret}",
            token_hash=hashlib.sha256(secret).hexdigest(),
        )

    def resolve(self, raw_token: str, *, lock: bool = False) -> InvitationModel:
        invitation_id, secret = self._parse(raw_token)
        statement = select(InvitationModel).where(InvitationModel.id == invitation_id)
        if lock:
            statement = statement.with_for_update()

        invitation = self.session.scalar(statement)
        if invitation is None:
            raise InvitationTokenError("invalid invitation token")

        candidate_hash = hashlib.sha256(secret).hexdigest()
        if not hmac.compare_digest(invitation.token_hash, candidate_hash):
            raise InvitationTokenError("invalid invitation token")
        return invitation

    @classmethod
    def _parse(cls, raw_token: str) -> tuple[str, bytes]:
        if not isinstance(raw_token, str) or raw_token.count(".") != 1:
            raise InvitationTokenError("invalid invitation token")

        invitation_id, encoded_secret = raw_token.split(".", 1)
        try:
            normalized_id = str(UUID(invitation_id))
        except (ValueError, AttributeError) as exc:
            raise InvitationTokenError("invalid invitation token") from exc

        try:
            secret = cls._decode_secret(encoded_secret)
        except (ValueError, base64.binascii.Error) as exc:
            raise InvitationTokenError("invalid invitation token") from exc

        if len(secret) != cls.SECRET_BYTES:
            raise InvitationTokenError("invalid invitation token")
        return normalized_id, secret

    @staticmethod
    def _encode_secret(secret: bytes) -> str:
        return base64.urlsafe_b64encode(secret).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode_secret(value: str) -> bytes:
        if not value:
            raise ValueError("empty invitation secret")
        padding = "=" * (-len(value) % 4)
        return base64.b64decode(value + padding, altchars=b"-_", validate=True)
