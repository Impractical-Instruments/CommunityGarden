"""
Grid touch tracker — debounces raw per-frame touch detections into stable
grid-cell DOWN / UP events suitable for driving game input.

A cell transitions DOWN only after it has been occupied for `confirm_frames`
consecutive frames, preventing phantom detections from sensor noise.

A cell transitions UP only after it has been absent for `release_frames`
consecutive frames, preventing mid-tap flicker from causing spurious releases.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class EventType(enum.Enum):
    DOWN = "down"
    UP = "up"


@dataclass(frozen=True)
class GridTouchEvent:
    type: EventType
    col: int
    row: int


class GridTouchTracker:
    """
    Maps a set of currently-touched grid cells each frame to DOWN/UP events.

    Usage:
        tracker = GridTouchTracker(cols=4, rows=4)

        # Each frame, pass the set of grid cells (col, row) that have an
        # active raw touch detection:
        events = tracker.update({(1, 2), (3, 0)})

        for ev in events:
            if ev.type == EventType.DOWN:
                send_osc("/captcha/touch/down", ev.col, ev.row)
            else:
                send_osc("/captcha/touch/up", ev.col, ev.row)
    """

    def __init__(
        self,
        cols: int,
        rows: int,
        confirm_frames: int = 3,
        release_frames: int = 8,
    ) -> None:
        self._cols = cols
        self._rows = rows
        self.confirm_frames = confirm_frames
        self.release_frames = release_frames

        # Cells with a confirmed DOWN that have not yet fired UP.
        self._confirmed: set[tuple[int, int]] = set()
        # Consecutive frames a cell has been seen (before confirmation).
        self._pending_down: dict[tuple[int, int], int] = {}
        # Consecutive frames a confirmed cell has been absent (before release).
        self._pending_up: dict[tuple[int, int], int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def rows(self) -> int:
        return self._rows

    def resize(self, cols: int, rows: int) -> None:
        """
        Update the active grid dimensions.
        Clears all pending and confirmed state since cell coordinates change.
        """
        self._cols = cols
        self._rows = rows
        self._confirmed.clear()
        self._pending_down.clear()
        self._pending_up.clear()

    def confirmed_cells(self) -> frozenset[tuple[int, int]]:
        """Return the set of currently confirmed (DOWN) grid cells."""
        return frozenset(self._confirmed)

    def update(
        self, active_cells: set[tuple[int, int]]
    ) -> list[GridTouchEvent]:
        """
        Process one frame of raw touch detections.

        active_cells: set of (col, row) tuples with a raw touch this frame.
        Returns a list of GridTouchEvent (DOWN/UP) that fired this frame.
        """
        events: list[GridTouchEvent] = []

        # --- cells seen this frame ---
        for cell in active_cells:
            if not self._in_bounds(cell):
                continue

            if cell in self._confirmed:
                # Already confirmed: reset any pending release counter.
                self._pending_up.pop(cell, None)
            else:
                # Accumulate toward confirmation.
                count = self._pending_down.get(cell, 0) + 1
                if count >= self.confirm_frames:
                    self._confirmed.add(cell)
                    self._pending_down.pop(cell, None)
                    events.append(GridTouchEvent(type=EventType.DOWN, col=cell[0], row=cell[1]))
                else:
                    self._pending_down[cell] = count

        # --- confirmed cells absent this frame ---
        for cell in list(self._confirmed):
            if cell not in active_cells:
                count = self._pending_up.get(cell, 0) + 1
                if count >= self.release_frames:
                    self._confirmed.discard(cell)
                    self._pending_up.pop(cell, None)
                    events.append(GridTouchEvent(type=EventType.UP, col=cell[0], row=cell[1]))
                else:
                    self._pending_up[cell] = count

        # --- pending_down cells absent this frame: reset their counter ---
        for cell in list(self._pending_down):
            if cell not in active_cells:
                del self._pending_down[cell]

        return events

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _in_bounds(self, cell: tuple[int, int]) -> bool:
        col, row = cell
        return 0 <= col < self._cols and 0 <= row < self._rows
