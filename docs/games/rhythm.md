# Rhythm — game design

**Status:** Code deleted (2026-05-11). Port to silhouette interaction TODO.

## Concept

A rhythm/music game. Notes fall down columns; Players must "tap" the correct column when a note reaches the trigger row. Hit enough notes to win before the song ends.

## Mechanics (as of deletion)

- **Grid:** 4×5 (4 columns, 5 rows). Bottom row is the trigger row.
- **Input:** Tap-based. Tap a column cell in the trigger row when a falling note is near it.
- **Notes:** Defined by `_SONG` (a sequence of column indices; -1 = rest). Notes spawn at the top and advance downward. Beat speed increases as the song progresses (ease-in).
- **Scoring:** Hit = +1. Miss (note scrolls past trigger) = -2. Wrong tap = -1. Win threshold: 18 points.
- **Win condition:** Score ≥ 18 by song end.
- **Loss condition:** Song repeats if score < 18 at end (no explicit timer in original code — self-termination relied on repeated failures eventually triggering loss state; this should be revisited during port to add a hard timer).
- **Audio:** Simple synthesised tones (triangle wave) per column. Plays on hit.

## Images

Photos from `rhythm-images.json` (list of filenames) displayed as column icons and on falling notes. Falls back to note labels (C/D/E/G) if empty.

## Port TODO

Replace tap detection with silhouette edge detection: detect when a Player's silhouette newly covers a trigger-row cell (transition from uncovered → covered = "tap event"). This preserves the timing-based interaction. The silhouette must move into the cell rather than hold it — otherwise the Player would trigger continuous hits. Hard timer (per ADR-0003) should be added during port.
