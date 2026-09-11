from __future__ import annotations

from fastapi.testclient import TestClient

from myhub.app.main import create_app
from myhub.modules.administration.config import Settings
from myhub.modules.identity.asset_links import build_asset_links_document, normalize_sha256_fingerprint


FINGERPRINT_COMPACT = "AA" * 32
FINGERPRINT_COLON = ":".join(["AA"] * 32)


def test_fingerprint_is_normalized() -> None:
    assert normalize_sha256_fingerprint(FINGERPRINT_COMPACT.lower()) == FINGERPRINT_COLON


def test_asset_links_uses_login_credentials_relation() -> None:
    document = build_asset_links_document(
        package_name="com.example.myhub",
        fingerprints=FINGERPRINT_COMPACT,
    )
    assert document == [
        {
            "relation": ["delegate_permission/common.get_login_creds"],
            "target": {
                "namespace": "android_app",
                "package_name": "com.example.myhub",
                "sha256_cert_fingerprints": [FINGERPRINT_COLON],
            },
        }
    ]


def test_unconfigured_asset_links_is_empty() -> None:
    assert build_asset_links_document(package_name=None, fingerprints="") == []


def test_well_known_endpoint_serves_configured_association(engine) -> None:
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        bootstrap_token="test-bootstrap-token-that-is-long-enough-12345",
        android_package_name="com.example.myhub",
        android_sha256_cert_fingerprints=FINGERPRINT_COMPACT,
    )
    app = create_app(settings=settings, engine=engine)
    with TestClient(app) as client:
        response = client.get("/.well-known/assetlinks.json")

    assert response.status_code == 200
    assert response.json()[0]["relation"] == ["delegate_permission/common.get_login_creds"]
    assert response.json()[0]["target"]["package_name"] == "com.example.myhub"
