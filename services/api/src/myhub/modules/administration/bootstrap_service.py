from __future__ import annotations

import hmac
import json
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from myhub.domain.bootstrap import BootstrapLifecycle, BootstrapState
from myhub.domain.identity import InstanceIdentityProvider
from myhub.modules.administration.bootstrap_repository import BootstrapRepository
from myhub.modules.administration.config import validate_canonical_url

logger = logging.getLogger("myhub.bootstrap")


class BootstrapError(RuntimeError):
    code = "BOOTSTRAP_ERROR"
    status_code = 500


class BootstrapUnauthorized(BootstrapError):
    code = "BOOTSTRAP_UNAUTHORIZED"
    status_code = 401


class InstanceAlreadyInitialized(BootstrapError):
    code = "INSTANCE_ALREADY_INITIALIZED"
    status_code = 409


class BootstrapInProgress(BootstrapError):
    code = "BOOTSTRAP_IN_PROGRESS"
    status_code = 409


@dataclass(frozen=True, slots=True)
class BootstrapCommand:
    family_name: str
    canonical_url: str
    owner_display_name: str
    supplied_token: str
    request_id: str


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    state: BootstrapState
    instance_id: str
    family_id: str
    owner_user_id: str
    owner_membership_id: str
    canonical_url: str
    server_public_key: str


class BootstrapService:
    def __init__(self, *, session: Session, identity_provider: InstanceIdentityProvider, expected_token: str):
        self.session = session
        self.repository = BootstrapRepository(session)
        self.identity_provider = identity_provider
        self.expected_token = expected_token

    def bootstrap(self, command: BootstrapCommand) -> BootstrapResult:
        if not hmac.compare_digest(command.supplied_token, self.expected_token):
            self._audit("bootstrap.authorization_failed", command.request_id)
            raise BootstrapUnauthorized("invalid bootstrap token")

        family_name = command.family_name.strip()
        owner_display_name = command.owner_display_name.strip()
        canonical_url = validate_canonical_url(command.canonical_url)

        try:
            with self.session.begin():
                record = self.repository.lock()
                current = BootstrapState(record.state)
                if current is BootstrapState.READY:
                    raise InstanceAlreadyInitialized("instance is already initialized")
                if current is BootstrapState.BOOTSTRAPPING:
                    raise BootstrapInProgress("bootstrap is already in progress")

                lifecycle = BootstrapLifecycle(current).transition_to(BootstrapState.BOOTSTRAPPING)
                record.state = lifecycle.state.value
                self.session.flush()
                self._audit("bootstrap.started", command.request_id)

                identity = self.identity_provider.generate()
                family = self.repository.create_family(family_name)
                owner, membership = self.repository.create_owner(family.id, owner_display_name)

                record.instance_id = identity.instance_id
                record.canonical_url = canonical_url
                record.family_id = family.id
                record.owner_user_id = owner.id
                record.owner_membership_id = membership.id
                record.server_public_key = identity.public_key
                record.server_private_key_pem = identity.private_key_pem
                record.state = lifecycle.transition_to(BootstrapState.READY).state.value

                result = BootstrapResult(
                    state=BootstrapState.READY,
                    instance_id=identity.instance_id,
                    family_id=family.id,
                    owner_user_id=owner.id,
                    owner_membership_id=membership.id,
                    canonical_url=canonical_url,
                    server_public_key=identity.public_key,
                )

            self._audit("bootstrap.completed", command.request_id, instance_id=result.instance_id, family_id=result.family_id, owner_user_id=result.owner_user_id)
            return result
        except (InstanceAlreadyInitialized, BootstrapInProgress):
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            self._audit("bootstrap.failed", command.request_id)
            raise

    @staticmethod
    def _audit(event: str, request_id: str, **fields: str) -> None:
        logger.info(json.dumps({"event": event, "request_id": request_id, **fields}, sort_keys=True))
