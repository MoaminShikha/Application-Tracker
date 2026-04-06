"""Tests for BaseService pooled connection safety behavior."""

import pytest
from psycopg2 import extensions

from job_tracker.services.base_service import BaseService


class _FakeConn:
    def __init__(self, rollback_raises=False, closed=0, tx_status=extensions.TRANSACTION_STATUS_IDLE):
        self.rollback_raises = rollback_raises
        self.closed = closed
        self.tx_status = tx_status
        self.rollback_calls = 0
        self.commit_calls = 0

    def rollback(self):
        self.rollback_calls += 1
        if self.rollback_raises:
            raise RuntimeError("rollback failed")

    def commit(self):
        self.commit_calls += 1

    def get_transaction_status(self):
        return self.tx_status


class _FakePool:
    def __init__(self, conn):
        self.conn = conn
        self.put_calls = []

    def getconn(self):
        return self.conn

    def putconn(self, conn, close=False):
        self.put_calls.append({"conn": conn, "close": close})


class _TestService(BaseService):
    pass


@pytest.fixture(autouse=True)
def _reset_pool():
    BaseService._pool = None
    yield
    BaseService._pool = None


def test_executor_rolls_back_and_reuses_connection_on_failure():
    conn = _FakeConn()
    pool = _FakePool(conn)
    BaseService._pool = pool
    svc = _TestService()

    with pytest.raises(RuntimeError):
        with svc._executor():
            raise RuntimeError("boom")

    assert conn.rollback_calls == 1
    assert pool.put_calls[-1]["close"] is False


def test_executor_discards_connection_when_rollback_fails():
    conn = _FakeConn(rollback_raises=True)
    pool = _FakePool(conn)
    BaseService._pool = pool
    svc = _TestService()

    with pytest.raises(RuntimeError):
        with svc._executor():
            raise RuntimeError("boom")

    assert conn.rollback_calls == 1
    assert pool.put_calls[-1]["close"] is True


def test_transaction_discards_connection_when_connection_is_unknown():
    conn = _FakeConn(tx_status=extensions.TRANSACTION_STATUS_UNKNOWN)
    pool = _FakePool(conn)
    BaseService._pool = pool
    svc = _TestService()

    with svc._transaction():
        pass

    assert conn.commit_calls == 1
    assert pool.put_calls[-1]["close"] is True

