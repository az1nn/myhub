from __future__ import annotations

from sqlalchemy.orm import Session

from myhub.domain.identity import InstanceIdentity
from myhub.infrastructure.db.models import InstanceBootstrapModel
from tests.conftest import TEST_TOKEN


class FailingIdentityProvider:
    def generate(self) -> InstanceIdentity:
        raise RuntimeError("simulated identity generation failure")


def payload() -> dict[str, str]:
    return {"family_name": "Family Test", "canonical_url": "https://family.example.com", "owner_display_name": "Initial Owner"}


def test_fresh_instance_is_uninitialized(client) -> None:
    response = client.get("/api/v1/instance")
    assert response.status_code == 200
    assert response.json()["state"] == "UNINITIALIZED"
    assert response.json()["instance_id"] is None


def test_bootstrap_requires_valid_token(client) -> None:
    response = client.post("/api/v1/bootstrap", headers={"X-MyHub-Bootstrap-Token": "x" * 40}, json=payload())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "BOOTSTRAP_UNAUTHORIZED"
    assert response.json()["error"]["request_id"]


def test_missing_bootstrap_token_is_unauthorized(client) -> None:
    response = client.post("/api/v1/bootstrap", json=payload())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "BOOTSTRAP_UNAUTHORIZED"


def test_blank_family_name_is_validation_error(client) -> None:
    invalid = payload()
    invalid["family_name"] = "   "
    response = client.post("/api/v1/bootstrap", headers={"X-MyHub-Bootstrap-Token": TEST_TOKEN}, json=invalid)
    assert response.status_code == 422


def test_success_then_rebootstrap_is_rejected(client) -> None:
    headers = {"X-MyHub-Bootstrap-Token": TEST_TOKEN}
    first = client.post("/api/v1/bootstrap", headers=headers, json=payload())
    assert first.status_code == 201
    assert first.json()["state"] == "READY"

    second = client.post("/api/v1/bootstrap", headers=headers, json=payload())
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "INSTANCE_ALREADY_INITIALIZED"

    status = client.get("/api/v1/instance")
    assert status.status_code == 200
    assert status.json()["state"] == "READY"
    assert status.json()["family_name"] == "Family Test"
    assert "server_private_key_pem" not in status.json()


def test_failed_transaction_does_not_report_ready_and_can_retry(client, engine) -> None:
    client.app.state.identity_provider = FailingIdentityProvider()
    headers = {"X-MyHub-Bootstrap-Token": TEST_TOKEN}

    failure = client.post("/api/v1/bootstrap", headers=headers, json=payload())
    assert failure.status_code == 500
    assert failure.json()["error"]["code"] == "INTERNAL_ERROR"
    assert failure.json()["error"]["request_id"]

    with Session(engine) as session:
        record = session.get(InstanceBootstrapModel, 1)
        assert record is not None
        assert record.state == "UNINITIALIZED"
        assert record.instance_id is None

    from myhub.infrastructure.identity import Ed25519InstanceIdentityProvider
    client.app.state.identity_provider = Ed25519InstanceIdentityProvider()
    retry = client.post("/api/v1/bootstrap", headers=headers, json=payload())
    assert retry.status_code == 201
    assert retry.json()["state"] == "READY"
