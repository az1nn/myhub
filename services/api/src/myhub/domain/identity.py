from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class InstanceIdentity:
    instance_id: str
    public_key: str
    private_key_pem: str


class InstanceIdentityProvider(Protocol):
    def generate(self) -> InstanceIdentity: ...
