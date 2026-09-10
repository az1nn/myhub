from __future__ import annotations

import base64
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from myhub.domain.identity import InstanceIdentity


class Ed25519InstanceIdentityProvider:
    """Generate instance identity material without exposing private key material."""

    def generate(self) -> InstanceIdentity:
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")
        public_raw = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        public_key_b64 = base64.urlsafe_b64encode(public_raw).decode("ascii").rstrip("=")

        return InstanceIdentity(
            instance_id=str(uuid.uuid4()),
            public_key=public_key_b64,
            private_key_pem=private_pem,
        )
