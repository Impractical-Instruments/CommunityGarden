"""Collects the OSC signals other Elements send, expires the ones that go quiet, and snapshots them as a GardenState."""

import logging
import time

from controllables import GardenState, ShowMode

log = logging.getLogger("treehouse")


class SignalIntake:
    """
    Holds the latest value from each sending Element (ADR-0007).

    A sender that has been silent for more than 2 x heartbeat_interval_s has its
    contribution zeroed, with one warning per silence.  A sender that has never
    sent is not stale: an Element that is not running is not a dead sender.
    """

    def __init__(self, heartbeat_interval_s: float = 5.0, clock=None) -> None:
        self._heartbeat_interval = heartbeat_interval_s
        self._clock = clock or time.monotonic
        self._flowerbeds_activity = 0.0
        self._captcha_intensity = 0.0
        self._pipes_activity = 0.0
        self._captcha_blowup_pending = False
        self._last_received: dict[str, float] = {}
        self._stale_warned: set[str] = set()

    def set_flowerbeds_activity(self, value: float) -> None:
        self._flowerbeds_activity = max(0.0, min(1.0, value))
        self._touch("flowerbeds")

    def set_captcha_intensity(self, value: float) -> None:
        self._captcha_intensity = max(0.0, min(1.0, value))
        self._touch("captcha")

    def set_pipes_activity(self, value: float) -> None:
        self._pipes_activity = max(0.0, min(1.0, value))
        self._touch("pipes")

    def trigger_captcha_blowup(self) -> None:
        """Latches the one-shot Blow-Up until the next snapshot(); also counts as a captcha heartbeat."""
        log.info("Captcha blowup signalled")
        self._captcha_blowup_pending = True
        self._touch("captcha")

    def snapshot(
        self, show_mode: ShowMode = ShowMode.ACTIVE, brightness: float = 1.0,
    ) -> GardenState:
        """
        The GardenState for this frame: stale senders expired first, the
        Blow-Up one-shot consumed (it is True in exactly one snapshot).
        Show mode and brightness are not signals; the caller supplies them.
        """
        self._expire_stale_senders()
        state = GardenState(
            flowerbeds_activity=self._flowerbeds_activity,
            captcha_intensity=self._captcha_intensity,
            captcha_blowup=self._captcha_blowup_pending,
            pipes_activity=self._pipes_activity,
            show_mode=show_mode,
            brightness=brightness,
        )
        self._captcha_blowup_pending = False
        return state

    def _touch(self, sender: str) -> None:
        self._last_received[sender] = self._clock()
        self._stale_warned.discard(sender)

    def _expire_stale_senders(self) -> None:
        now = self._clock()
        timeout = 2.0 * self._heartbeat_interval
        for sender, last in self._last_received.items():
            if now - last <= timeout:
                continue
            if sender not in self._stale_warned:
                log.warning(
                    "No signal from %s for %.0fs — zeroing contribution",
                    sender, now - last,
                )
                self._stale_warned.add(sender)
            if sender == "flowerbeds":
                self._flowerbeds_activity = 0.0
            elif sender == "captcha":
                self._captcha_intensity = 0.0
            elif sender == "pipes":
                self._pipes_activity = 0.0
