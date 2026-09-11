from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type


class LoginNameError(ValueError):
    pass


def normalize_login_name(value: str) -> str:
    """Return the canonical instance-local login identifier.

    The rule is intentionally Unicode-aware: NFKC + trim + casefold. Internal
    whitespace and Unicode control/format characters are rejected so visually
    hidden separators do not create ambiguous account identifiers.
    """

    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    if not 3 <= len(normalized) <= 120:
        raise LoginNameError("login_name_length")
    if any(char.isspace() or unicodedata.category(char).startswith("C") for char in normalized):
        raise LoginNameError("login_name_contains_disallowed_character")
    return normalized


@dataclass(frozen=True, slots=True)
class Argon2idPolicy:
    # OWASP minimum baseline: 19 MiB, t=2, p=1.
    memory_cost_kib: int = 19_456
    time_cost: int = 2
    parallelism: int = 1
    hash_len: int = 32
    salt_len: int = 16


class PasswordService:
    def __init__(self, policy: Argon2idPolicy | None = None) -> None:
        self.policy = policy or Argon2idPolicy()
        self._hasher = PasswordHasher(
            time_cost=self.policy.time_cost,
            memory_cost=self.policy.memory_cost_kib,
            parallelism=self.policy.parallelism,
            hash_len=self.policy.hash_len,
            salt_len=self.policy.salt_len,
            type=Type.ID,
        )

    def hash(self, password: str) -> str:
        if not password:
            raise ValueError("password must not be empty")
        return self._hasher.hash(password)

    def verify(self, encoded_hash: str, password: str) -> bool:
        if not password:
            return False
        try:
            return self._hasher.verify(encoded_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, encoded_hash: str) -> bool:
        try:
            return self._hasher.check_needs_rehash(encoded_hash)
        except InvalidHashError:
            return True
