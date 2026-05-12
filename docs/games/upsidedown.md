# UpsideDown — game design

**Status:** Code deleted (2026-05-11). Port to silhouette interaction TODO.

## Concept

A memory/matching game. The grid shows image pairs — but every piece is displayed rotated 180°. Players must find and match the pairs before the timer runs out.

## Mechanics (as of deletion)

- **Grid:** 4×4 (16 cells, 8 pairs)
- **Input:** Tap-based. Tap a cell to select it; tap another to attempt a match. Correct pair (same `pair_id`, different `half`) → both cells lock. Wrong pair → flash red, deselect.
- **Win condition:** All 8 pairs matched before timer expires.
- **Loss condition:** 45s timer expires → vortex animation (unfixed cells spin and shrink) → Blow-Up.
- **Difficulty scaling (per Arc):** Not yet implemented in the deleted code; was intended.

## Images

Photos live in `images/`. `pairs.json` maps filenames: `[{"label": str, "a": "file_a.jpg", "b": "file_b.jpg"}]`. Falls back to text labels if fewer than 8 pairs or files missing.

## Port TODO

Replace tap detection with silhouette dwell: a cell is "selected" when a Player's silhouette covers it for ≥ `select_dwell_s`. Selected cell highlights; a second covered cell triggers the match attempt. All other mechanics unchanged. The game is naturally suited to 1–2 Players (one selecting, one confirming, or one person doing both).
