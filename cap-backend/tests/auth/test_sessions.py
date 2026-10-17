from app.auth.rate_limit import LoginRateLimiter
from app.auth.sessions import SessionStore
from tests.support.fake_time import FakeTime


def test_new_sessions_are_valid_and_unpredictable() -> None:
    store = SessionStore(60, FakeTime())

    first, second = store.create(), store.create()

    assert store.is_valid(first) and store.is_valid(second)
    assert first != second
    assert len(first) >= 40


def test_unknown_or_missing_ids_are_invalid() -> None:
    store = SessionStore(60, FakeTime())

    assert not store.is_valid(None)
    assert not store.is_valid("made-up")


def test_sessions_expire_after_their_ttl() -> None:
    fake_time = FakeTime()
    store = SessionStore(60, fake_time)
    session_id = store.create()

    fake_time.now = 59
    assert store.is_valid(session_id)
    fake_time.now = 60
    assert not store.is_valid(session_id)


def test_revoked_sessions_stop_working() -> None:
    store = SessionStore(60, FakeTime())
    session_id = store.create()

    store.revoke(session_id)
    store.revoke(None)

    assert not store.is_valid(session_id)


def test_login_is_blocked_after_too_many_failures_and_recovers() -> None:
    fake_time = FakeTime()
    limiter = LoginRateLimiter(3, fake_time)

    for _ in range(3):
        assert not limiter.is_blocked("10.0.0.1")
        limiter.record_failure("10.0.0.1")

    assert limiter.is_blocked("10.0.0.1")
    assert not limiter.is_blocked("10.0.0.2")
    fake_time.now = 61
    assert not limiter.is_blocked("10.0.0.1")


def test_a_successful_login_clears_the_failures() -> None:
    limiter = LoginRateLimiter(2, FakeTime())
    limiter.record_failure("a")
    limiter.record_failure("a")

    limiter.reset("a")

    assert not limiter.is_blocked("a")
