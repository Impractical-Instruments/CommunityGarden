"""
One SIGINT/SIGTERM handler that turns a Ctrl+C or `systemctl stop` into a flag a loop can poll.
"""

from __future__ import annotations

import logging
import signal

log = logging.getLogger("flower_beds")


class StopSignal:
    """Install on construction; `bool(stop)` is True once SIGINT or SIGTERM has arrived."""

    def __init__(self, message: str | None = None) -> None:
        self._message = message
        self.requested = False
        signal.signal(signal.SIGINT, self._handle)
        signal.signal(signal.SIGTERM, self._handle)

    def _handle(self, signum, frame) -> None:
        if self._message:
            log.info(self._message)
        self.requested = True

    def __bool__(self) -> bool:
        return self.requested
