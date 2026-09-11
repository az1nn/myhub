from __future__ import annotations

import re

from fastapi import APIRouter, Request


well_known_router = APIRouter()

_PACKAGE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")
_HEX_RE = re.compile(r"^[0-9A-F]{64}$")


def normalize_sha256_fingerprint(value: str) -> str:
    compact = value.strip().replace(":", "").upper()
    if not _HEX_RE.fullmatch(compact):
        raise ValueError("Android signing fingerprint must contain exactly 32 SHA-256 bytes")
    return ":".join(compact[index : index + 2] for index in range(0, 64, 2))


def parse_fingerprints(value: str) -> list[str]:
    if not value.strip():
        return []
    normalized = [normalize_sha256_fingerprint(item) for item in value.split(",") if item.strip()]
    # Preserve configured order but remove duplicates.
    return list(dict.fromkeys(normalized))


def build_asset_links_document(*, package_name: str | None, fingerprints: str) -> list[dict[str, object]]:
    if package_name is None and not fingerprints.strip():
        return []
    if not package_name or not _PACKAGE_RE.fullmatch(package_name):
        raise ValueError("MYHUB_ANDROID_PACKAGE_NAME is invalid")

    parsed_fingerprints = parse_fingerprints(fingerprints)
    if not parsed_fingerprints:
        raise ValueError("at least one Android SHA-256 signing fingerprint is required")

    return [
        {
            "relation": ["delegate_permission/common.get_login_creds"],
            "target": {
                "namespace": "android_app",
                "package_name": package_name,
                "sha256_cert_fingerprints": parsed_fingerprints,
            },
        }
    ]


@well_known_router.get("/.well-known/assetlinks.json", include_in_schema=False)
def get_asset_links(request: Request) -> list[dict[str, object]]:
    settings = request.app.state.settings
    return build_asset_links_document(
        package_name=settings.android_package_name,
        fingerprints=settings.android_sha256_cert_fingerprints,
    )
