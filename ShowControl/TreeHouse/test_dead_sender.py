"""Tests for SignalIntake's dead-sender policy (ADR-0007) — no hardware."""
from garden_state import SignalIntake


def _intake(heartbeat_interval_s=5.0, start_time=0.0):
    clock = _FakeClock(start_time)
    c = SignalIntake(heartbeat_interval_s=heartbeat_interval_s, clock=clock)
    return c, clock


class _FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


# ---------------------------------------------------------------------------
# Signals are preserved while within the timeout window
# ---------------------------------------------------------------------------

def test_all_three_signals_preserved_before_timeout():
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.5)
    c.set_captcha_intensity(0.6)
    c.set_pipes_activity(0.7)
    clock.advance(9.9)
    state = c.snapshot()
    assert state.flowerbeds_activity == 0.5
    assert state.captcha_intensity == 0.6
    assert state.pipes_activity == 0.7


# ---------------------------------------------------------------------------
# Stale signals are zeroed after 2 × heartbeat_interval_s
# ---------------------------------------------------------------------------

def test_flowerbeds_zeroed_after_timeout():
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.9)
    clock.advance(10.1)
    state = c.snapshot()
    assert state.flowerbeds_activity == 0.0


def test_captcha_intensity_zeroed_after_timeout():
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_captcha_intensity(0.75)
    clock.advance(10.1)
    state = c.snapshot()
    assert state.captcha_intensity == 0.0


def test_pipes_zeroed_after_timeout():
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_pipes_activity(0.4)
    clock.advance(10.1)
    state = c.snapshot()
    assert state.pipes_activity == 0.0


def test_only_stale_sender_is_zeroed():
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.9)
    c.set_pipes_activity(0.5)
    clock.advance(6.0)
    # refresh pipes but not flowerbeds
    c.set_pipes_activity(0.5)
    clock.advance(4.5)  # flowerbeds now 10.5 s old, pipes only 4.5 s old
    state = c.snapshot()
    assert state.flowerbeds_activity == 0.0
    assert state.pipes_activity == 0.5


# ---------------------------------------------------------------------------
# blowup also counts as a captcha heartbeat
# ---------------------------------------------------------------------------

def test_captcha_blowup_resets_captcha_timeout():
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_captcha_intensity(0.8)
    clock.advance(8.0)
    c.trigger_captcha_blowup()  # refreshes the captcha timestamp
    clock.advance(4.0)  # 4 s since blowup, well within timeout
    state = c.snapshot()
    assert state.captcha_intensity == 0.8


# ---------------------------------------------------------------------------
# Recovery: signal resumes after a stale period
# ---------------------------------------------------------------------------

def test_signal_recovers_after_stale():
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.9)
    clock.advance(11.0)
    state = c.snapshot()  # goes stale → 0.0
    assert state.flowerbeds_activity == 0.0

    c.set_flowerbeds_activity(0.6)  # sender comes back
    state = c.snapshot()
    assert state.flowerbeds_activity == 0.6


# ---------------------------------------------------------------------------
# Warn once on first stale, clear on recovery
# ---------------------------------------------------------------------------

def test_stale_warning_issued_once(caplog):
    import logging
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.5)

    with caplog.at_level(logging.WARNING, logger="treehouse"):
        clock.advance(11.0)
        c.snapshot()  # first stale → warning
        clock.advance(5.0)
        c.snapshot()  # still stale → no second warning

    warnings = [r for r in caplog.records if "flowerbeds" in r.message and r.levelno == logging.WARNING]
    assert len(warnings) == 1


def test_stale_warning_reissued_after_recovery(caplog):
    import logging
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.5)

    with caplog.at_level(logging.WARNING, logger="treehouse"):
        clock.advance(11.0)
        c.snapshot()  # first stale period

        c.set_flowerbeds_activity(0.5)  # recover
        clock.advance(11.0)
        c.snapshot()  # second stale period → new warning

    warnings = [r for r in caplog.records if "flowerbeds" in r.message and r.levelno == logging.WARNING]
    assert len(warnings) == 2


# ---------------------------------------------------------------------------
# Senders that never sent are not affected (no phantom timeouts)
# ---------------------------------------------------------------------------

def test_never_sent_sender_is_not_reported_stale(caplog):
    # An Element that isn't running (never sent) is not a dead sender: no "No signal from" warning.
    import logging
    c, clock = _intake(heartbeat_interval_s=5.0)
    c.set_captcha_intensity(0.5)                    # captcha is live; flowerbeds never sends
    with caplog.at_level(logging.WARNING, logger="treehouse"):
        clock.advance(100.0)
        state = c.snapshot()
    stale = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert stale and all("flowerbeds" not in m and "pipes" not in m for m in stale), stale
