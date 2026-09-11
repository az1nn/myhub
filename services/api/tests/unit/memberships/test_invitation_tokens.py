from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from myhub.infrastructure.db.models import FamilyModel, InvitationModel, UserModel
from myhub.modules.invitations.tokens import InvitationTokenError, InvitationTokenService


FAMILY_ID = "30000000-0000-0000-0000-000000000001"
OWNER_ID = "30000000-0000-0000-0000-000000000002"


def _seed_invitation(session: Session):
    issued = InvitationTokenService.issue()
    with session.begin():
        session.add(FamilyModel(id=FAMILY_ID, name="Token Family"))
        session.add(UserModel(id=OWNER_ID, display_name="Owner"))
        session.flush()
        session.add(
            InvitationModel(
                id=issued.invitation_id,
                tenant_id=FAMILY_ID,
                created_by_user_id=OWNER_ID,
                intended_role="Member",
                token_hash=issued.token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
    return issued


def test_issue_uses_uuid_plus_256_bit_secret_and_hash_only_shape() -> None:
    first = InvitationTokenService.issue()
    second = InvitationTokenService.issue()

    assert first.invitation_id != second.invitation_id
    assert first.raw_token != second.raw_token
    assert first.raw_token.startswith(first.invitation_id + ".")
    assert len(first.token_hash) == 64
    assert first.token_hash not in first.raw_token


def test_resolve_finds_by_public_id_and_verifies_secret(engine) -> None:
    with Session(engine) as session:
        issued = _seed_invitation(session)
        resolved = InvitationTokenService(session).resolve(issued.raw_token)
        assert resolved.id == issued.invitation_id
        assert resolved.tenant_id == FAMILY_ID


def test_tampered_secret_fails_closed(engine) -> None:
    with Session(engine) as session:
        issued = _seed_invitation(session)
        invitation_id, secret = issued.raw_token.split(".", 1)
        replacement = ("A" if secret[0] != "A" else "B") + secret[1:]

        with pytest.raises(InvitationTokenError, match="invalid invitation token"):
            InvitationTokenService(session).resolve(f"{invitation_id}.{replacement}")


def test_unknown_id_and_malformed_token_have_same_public_error(engine) -> None:
    with Session(engine) as session:
        service = InvitationTokenService(session)
        for token in (
            "not-a-token",
            "00000000-0000-0000-0000-000000000000.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        ):
            with pytest.raises(InvitationTokenError, match="invalid invitation token"):
                service.resolve(token)
