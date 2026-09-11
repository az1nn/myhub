"""SQLite cannot model SELECT ... FOR UPDATE; PostgreSQL race coverage lives in test_postgres_concurrency.py."""

from myhub.modules.administration.bootstrap_repository import BOOTSTRAP_ROW_ID


def test_bootstrap_singleton_row_is_fixed() -> None:
    assert BOOTSTRAP_ROW_ID == 1
