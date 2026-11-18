"""The level list being edited, and every change an editor action can make to it; no drawing, no pygame display."""
from __future__ import annotations

from crop import ANCHORS, DEFAULT_ALIGN
from levels import Levels, level_sort_key, new_default_level

Cell = tuple[int, int]


class LevelModel:
    """The levels in memory, which one is selected, and whether there are unsaved edits.

    Actions that deserve feedback (new, delete, save) leave a message in
    `notice`; whoever draws takes it with `take_notice()`.
    """

    def __init__(self, levels: list[dict], store: Levels) -> None:
        self.levels = levels
        self.store  = store
        self.idx    = 0
        self.dirty  = False
        self.notice = ""

    @classmethod
    def open(cls, store: Levels) -> "LevelModel":
        """The model for `store`'s file; one default level if it is missing or unusable."""
        return cls(store.read() or [new_default_level()], store)

    def take_notice(self) -> str:
        msg, self.notice = self.notice, ""
        return msg

    # ── The selected level ─────────────────────────────────────────────────

    @property
    def level(self) -> dict:
        return self.levels[self.idx]

    @property
    def valid_cells(self) -> set[Cell]:
        return {tuple(c) for c in self.level.get("valid_cells", [])}

    def grid_dims(self) -> tuple[int, int]:
        return tuple(self.level.get("grid", [4, 4]))

    def align(self) -> str:
        a = self.level.get("crop_align")
        return a if a in ANCHORS else DEFAULT_ALIGN

    # ── Edits to the selected level ────────────────────────────────────────

    def _write_valid(self, cells: set[Cell]) -> None:
        self.level["valid_cells"] = sorted([list(c) for c in cells])
        self.dirty = True

    def set_align(self, align: str) -> None:
        # Center is the default; storing it would add a key to every level.
        if align == DEFAULT_ALIGN:
            self.level.pop("crop_align", None)
        else:
            self.level["crop_align"] = align
        self.dirty = True

    def set_prompt(self, text: str) -> None:
        self.level["prompt"] = text
        self.dirty = True

    def set_image(self, name: str | None) -> None:
        self.level["image"] = name
        self.dirty = True

    def toggle(self, cell: Cell) -> None:
        v = self.valid_cells
        v.discard(cell) if cell in v else v.add(cell)
        self._write_valid(v)

    def clear_cells(self) -> None:
        self._write_valid(set())

    def adj_difficulty(self, d: int) -> None:
        self.level["difficulty"] = max(1, min(5, self.level.get("difficulty", 1) + d))
        self.dirty = True

    def adj_cols(self, d: int) -> None:
        cols, rows = self.grid_dims()
        nc = max(2, min(8, cols + d))
        self.level["grid"] = [nc, rows]
        self._write_valid({(c, r) for c, r in self.valid_cells if c < nc})

    def adj_rows(self, d: int) -> None:
        cols, rows = self.grid_dims()
        nr = max(2, min(8, rows + d))
        self.level["grid"] = [cols, nr]
        self._write_valid({(c, r) for c, r in self.valid_cells if r < nr})

    def adj_timer(self, d: int) -> None:
        self.level["timer_s"] = max(5, self.level.get("timer_s", 40) + d)
        self.dirty = True

    def adj_hold(self, d: float) -> None:
        h = self.level.get("hold_s", 1.0)
        self.level["hold_s"] = round(max(0.5, h + d), 1)
        self.dirty = True

    def add_hold(self) -> None:
        self.level["hold_s"] = 1.0
        self.dirty = True

    def remove_hold(self) -> None:
        self.level.pop("hold_s", None)
        self.dirty = True

    # ── The list ───────────────────────────────────────────────────────────

    def nav(self, d: int) -> None:
        self.idx = (self.idx + d) % len(self.levels)

    def new_level(self) -> None:
        self.levels.insert(self.idx + 1, new_default_level())
        self.idx  += 1
        self.dirty = True
        self.notice = "New level added"

    def delete_level(self) -> None:
        if len(self.levels) <= 1:
            self.notice = "Can't delete only level"
            return
        del self.levels[self.idx]
        self.idx   = min(self.idx, len(self.levels) - 1)
        self.dirty = True
        self.notice = "Level deleted"

    def save(self) -> None:
        """Sort, write to the store, and keep the same level selected.

        A write that fails (OSError) is reported in `notice`, not raised: the
        editor must survive it to warn about unsaved changes on the way out.
        """
        current = self.level
        self.levels.sort(key=level_sort_key)
        self.idx = self.levels.index(current)
        try:
            self.store.write(self.levels)
        except OSError as exc:
            self.notice = f"SAVE FAILED: {exc}"
            return
        self.dirty = False
        self.notice = "Saved!"
