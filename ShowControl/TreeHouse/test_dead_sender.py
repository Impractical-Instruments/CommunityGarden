"""Tests for Coordinator dead-sender policy (ADR-0007) — no hardware."""
from coordinator import Coordinator


def _coord(heartbeat_interval_s=5.0, start_time=0.0):
    clock = _FakeClock(start_time)
    c = Coordinator([], heartbeat_interval_s=heartbeat_interval_s, _clock=clock)
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

def test_signal_preserved_before_timeout():
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.8)
    clock.advance(9.9)  # just under 2 × 5 s
    c.update(0.1)
    assert c._flowerbeds_activity == 0.8


def test_all_three_signals_preserved_before_timeout():
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.5)
    c.set_captcha_intensity(0.6)
    c.set_pipes_activity(0.7)
    clock.advance(9.9)
    c.update(0.1)
    assert c._flowerbeds_activity == 0.5
    assert c._captcha_intensity == 0.6
    assert c._pipes_activity == 0.7


# ---------------------------------------------------------------------------
# Stale signals are zeroed after 2 × heartbeat_interval_s
# ---------------------------------------------------------------------------

def test_flowerbeds_zeroed_after_timeout():
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.9)
    clock.advance(10.1)
    c.update(0.1)
    assert c._flowerbeds_activity == 0.0


def test_captcha_intensity_zeroed_after_timeout():
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_captcha_intensity(0.75)
    clock.advance(10.1)
    c.update(0.1)
    assert c._captcha_intensity == 0.0


def test_pipes_zeroed_after_timeout():
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_pipes_activity(0.4)
    clock.advance(10.1)
    c.update(0.1)
    assert c._pipes_activity == 0.0


def test_only_stale_sender_is_zeroed():
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.9)
    c.set_pipes_activity(0.5)
    clock.advance(6.0)
    # refresh pipes but not flowerbeds
    c.set_pipes_activity(0.5)
    clock.advance(4.5)  # flowerbeds now 10.5 s old, pipes only 4.5 s old
    c.update(0.1)
    assert c._flowerbeds_activity == 0.0
    assert c._pipes_activity == 0.5


# ---------------------------------------------------------------------------
# blowup also counts as a captcha heartbeat
# ---------------------------------------------------------------------------

def test_captcha_blowup_resets_captcha_timeout():
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_captcha_intensity(0.8)
    clock.advance(8.0)
    c.trigger_captcha_blowup()  # refreshes the captcha timestamp
    clock.advance(4.0)  # 4 s since blowup, well within timeout
    c.update(0.1)
    assert c._captcha_intensity == 0.8


# ---------------------------------------------------------------------------
# Recovery: signal resumes after a stale period
# ---------------------------------------------------------------------------

def test_signal_recovers_after_stale():
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.9)
    clock.advance(11.0)
    c.update(0.1)  # goes stale → 0.0
    assert c._flowerbeds_activity == 0.0

    c.set_flowerbeds_activity(0.6)  # sender comes back
    c.update(0.1)
    assert c._flowerbeds_activity == 0.6


# ---------------------------------------------------------------------------
# Warn once on first stale, clear on recovery
# ---------------------------------------------------------------------------

def test_stale_warning_issued_once(caplog):
    import logging
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.5)

    with caplog.at_level(logging.WARNING, logger="treehouse"):
        clock.advance(11.0)
        c.update(0.1)  # first stale → warning
        clock.advance(5.0)
        c.update(0.1)  # still stale → no second warning

    warnings = [r for r in caplog.records if "flowerbeds" in r.message and r.levelno == logging.WARNING]
    assert len(warnings) == 1


def test_stale_warning_reissued_after_recovery(caplog):
    import logging
    c, clock = _coord(heartbeat_interval_s=5.0)
    c.set_flowerbeds_activity(0.5)

    with caplog.at_level(logging.WARNING, logger="treehouse"):
        clock.advance(11.0)
        c.update(0.1)  # first stale period

        c.set_flowerbeds_activity(0.5)  # recover
        clock.advance(11.0)
        c.update(0.1)  # second stale period → new warning

    warnings = [r for r in caplog.records if "flowerbeds" in r.message and r.levelno == logging.WARNING]
    assert len(warnings) == 2


# ---------------------------------------------------------------------------
# Senders that never sent are not affected (no phantom timeouts)
# ---------------------------------------------------------------------------

def test_never_sent_sender_not_zeroed():
    c, clock = _coord(heartbeat_interval_s=5.0)
    # Don't call set_flowerbeds_activity at all
    clock.advance(100.0)
    c.update(0.1)
    # Still at default 0.0 — no crash, no spurious zeroing
    assert c._flowerbeds_activity == 0.0
