import pytest

from myhub.domain.bootstrap import BootstrapLifecycle, BootstrapState, InvalidBootstrapTransition


def test_happy_path_state_machine() -> None:
    lifecycle = BootstrapLifecycle(BootstrapState.UNINITIALIZED)
    lifecycle = lifecycle.transition_to(BootstrapState.BOOTSTRAPPING)
    lifecycle = lifecycle.transition_to(BootstrapState.READY)
    assert lifecycle.state is BootstrapState.READY


def test_bootstrapping_may_return_to_uninitialized_for_retry_semantics() -> None:
    lifecycle = BootstrapLifecycle(BootstrapState.BOOTSTRAPPING)
    assert lifecycle.transition_to(BootstrapState.UNINITIALIZED).state is BootstrapState.UNINITIALIZED


def test_ready_is_terminal_for_first_time_bootstrap() -> None:
    with pytest.raises(InvalidBootstrapTransition):
        BootstrapLifecycle(BootstrapState.READY).transition_to(BootstrapState.BOOTSTRAPPING)
