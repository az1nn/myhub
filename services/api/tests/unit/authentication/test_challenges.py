from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from myhub.modules.identity.challenges import ChallengeError, ChallengePurpose, ChallengeService


NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


def test_challenge_is_random_hashed_and_single_use(engine) -> None:
    with Session(engine) as session, session.begin():
        service = ChallengeService(session, ttl_seconds=300)
        issued = service.issue(purpose=ChallengePurpose.AUTHENTICATION, user_id=None, now=NOW)

        assert issued.token
        assert len(issued.raw) == 32
        assert issued.token != issued.raw.hex()
        assert service.consume(
            token=issued.token,
            purpose=ChallengePurpose.AUTHENTICATION,
            user_id=None,
            now=NOW + timedelta(seconds=1),
        ) == issued.raw

        with pytest.raises(ChallengeError) as replay:
            service.consume(
                token=issued.token,
                purpose=ChallengePurpose.AUTHENTICATION,
                user_id=None,
                now=NOW + timedelta(seconds=2),
            )
        assert replay.value.code == "challenge_replayed"


def test_expired_challenge_is_rejected(engine) -> None:
    with Session(engine) as session, session.begin():
        service = ChallengeService(session, ttl_seconds=30)
        issued = service.issue(purpose=ChallengePurpose.REGISTRATION, user_id=None, now=NOW)

        with pytest.raises(ChallengeError) as expired:
            service.consume(
                token=issued.token,
                purpose=ChallengePurpose.REGISTRATION,
                user_id=None,
                now=NOW + timedelta(seconds=31),
            )
        assert expired.value.code == "challenge_expired"


def test_challenge_is_bound_to_ceremony(engine) -> None:
    with Session(engine) as session, session.begin():
        service = ChallengeService(session)
        issued = service.issue(purpose=ChallengePurpose.REGISTRATION, user_id=None, now=NOW)

        with pytest.raises(ChallengeError) as mismatch:
            service.consume(
                token=issued.token,
                purpose=ChallengePurpose.AUTHENTICATION,
                user_id=None,
                now=NOW + timedelta(seconds=1),
            )
        assert mismatch.value.code == "invalid_challenge"


def test_invalid_transport_token_is_rejected(engine) -> None:
    with Session(engine) as session:
        service = ChallengeService(session)
        with pytest.raises(ChallengeError) as invalid:
            service.consume(
                token="not-a-valid-32-byte-challenge",
                purpose=ChallengePurpose.AUTHENTICATION,
                user_id=None,
                now=NOW,
            )
        assert invalid.value.code == "invalid_challenge"
