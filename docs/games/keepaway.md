# Keepaway — game design

**Status:** Code deleted (2026-05-11). Port to silhouette interaction TODO.

## Concept

A football keepaway game. Players control an offense team trying to survive with the ball while defenders automatically chase them. Pass the ball to open teammates to avoid being caught.

## Mechanics (as of deletion)

- **Grid:** 5×5
- **Pieces:** 5 offense pieces + 4 defense pieces. Ball starts with offense[0].
- **Input:** Tap-based, two-phase.
  - *Select phase:* Tap the ball carrier to select.
  - *Pass phase:* Tap an open (undefended) receiver to pass. Tapping a defended receiver flashes red (pass blocked).
- **Defense AI:** Each tick, defenders move one cell toward their target. Even-indexed defenders chase the ball; odd-indexed defenders chase the farthest open receiver. Tick speed scales with difficulty.
- **Win condition:** Survive for 12s without being caught (ball carrier shares cell with a defender).
- **Loss condition:** Ball carrier caught (defender on same cell). Flash red → short delay → Blow-Up.
- **Difficulty scaling:** `_difficulty` increments each Arc; defender tick speed increases (`_TICK_BASE_MS - difficulty × 80ms`, floor 300ms). Also applied with ease-in per round.

## Images

Photos from `keepaway-images.json` (list of filenames) displayed on offense pieces. Falls back to colored circles.

## Port TODO

Replace tap detection with silhouette dwell: *select phase* triggers when a Player's silhouette covers the ball carrier cell for ≥ `select_dwell_s`; *pass phase* triggers when silhouette covers a receiver cell for ≥ `pass_dwell_s`. Multiple Players can cooperate — one dwells on ball carrier, another dwells on receiver. This maps naturally to the multi-player silhouette model.
