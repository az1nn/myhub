from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BootstrapState(StrEnum):
    UNINITIALIZED = "UNINITIALIZED"
    BOOTSTRAPPING = "BOOTSTRAPPING"
    READY = "READY"


class InvalidBootstrapTransition(ValueError):
    pass


_ALLOWED_TRANSITIONS: dict[BootstrapState, frozenset[BootstrapState]] = {
    BootstrapState.UNINITIALIZED: frozenset({BootstrapState.BOOTSTRAPPING}),
    BootstrapState.BOOTSTRAPPING: frozenset(
        {BootstrapState.READY, BootstrapState.UNINITIALIZED}
    ),
    BootstrapState.READY: frozenset(),
}


@dataclass(frozen=True, slots=True)
class BootstrapLifecycle:
    state: BootstrapState

    def transition_to(self, target: BootstrapState) -> "BootstrapLifecycle":
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise InvalidBootstrapTransition(
                f"invalid bootstrap transition: {self.state} -> {target}"
            )
        return BootstrapLifecycle(state=target)
