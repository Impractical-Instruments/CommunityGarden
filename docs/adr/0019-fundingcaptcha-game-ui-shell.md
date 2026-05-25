# FundingCAPTCHA Games share a single UI shell — billboard prompt + maximal grid

## Context

The original BodyCaptcha layout (`games/bodycaptcha.py`, `games/grid.py`) carried over the early prototype's right-hand HUD column: a 220px vertical strip holding TIME, DIFFICULTY, HOLD bar, and prompt text. The Grid letterboxed inside the remaining left area.

Two problems showed up on the FundingCAPTCHA kiosk (4:3 short-throw projection):

- **The prompt was unreadable from Player distance.** Wrapped 16pt monospace inside a 220px column reads as filler text, not as instruction. Players didn't know what they were being asked to do.
- **The grid was cramped.** The HUD strip burned ~21% of screen width on data Players don't need to see (DIFFICULTY) or didn't notice (the HOLD bar tucked off to the side).

BodyCaptcha is the first FundingCAPTCHA Game with this shell, but `body_keepaway` already uses the same `Grid` + `HUD_W=220` primitives, and future Games are expected. The visual contract should be consistent across Games — Players are cycling through Arcs and the kiosk should feel like one machine, not four.

## Decision

All FundingCAPTCHA Games render against a single shared UI shell:

```
┌──────────────────────────────────────────────────────────┐
│   Select all squares containing a smile           23s   │   ← Top bar (12% of WH)
├──────────────────────────────────────────────────────────┤
│                                                          │
│              [ photo, clipped to grid bounds ]           │
│              [ grid cells + silhouette overlay ]         │
│              [ optional hold-ring on grid perimeter ]    │
│                                                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Top bar** (top 12% of screen, full width, solid black):
- Prompt text, centered horizontally and vertically. Auto-shrink-to-fit on one line, with a sensible upper font cap so short prompts don't become billboards.
- Level timer in the top-right corner, fairly small, GREEN when >10s remaining, RED when ≤10s. Number only (e.g. `23s`) — no bar, no ring.
- No separator line between bar and grid area — black-on-black reads as one composition with the photo edges as the only visible boundary.
- Prompt is **optional**: when absent (e.g. `keepaway_body` today), the bar still renders for layout consistency but only shows the timer.

**Grid area** (remaining ~88% of WH, full width):
- Photo (level background image) is clipped to grid bounds — no bleed past grid edges. The photo and the grid are one visual unit, not two stacked layers.
- Silhouette overlay (faint, alpha ~60) renders over the photo so Players can see how their body maps to cells.
- Cell-activation overlays unchanged: HINT_COLOR for valid-and-uncovered, COVER_VALID for valid-and-covered, COVER_EXTRA for invalid-and-covered, HOLD_COLOR when hold is active.

**Hold-ring overlay** (opt-in per Game):
- When all `valid_cells` are covered and no extras, a thick (~8–12px) clockwise-filling arc renders along the grid's outer perimeter in HOLD_COLOR.
- No background track — empty state = clean grid; full ring = win imminent.
- Only Games with a hold mechanic enable it. `keepaway_body` does not.

**Center overlays** (per-game moments):
- WIN_FLASH "LEVEL CLEAR!" renders as large centered text over the grid (cells already flashing green underneath).
- Blow-Up taunts render as large multi-line centered text over the confetti animation.
- Games may add their own per-Arc center overlays as needed.

The 220px HUD column (`HUD_W` in `games/grid.py`) is removed. `Grid` letterboxing logic now letterboxes inside the full-width-below-top-bar area.

## Alternatives considered

**Keep the HUD column, just enlarge the prompt.** Rejected. The HUD column cap was the bottleneck — at 220px wide, even with a bigger font the prompt has to wrap to 2–3 lines and competes with HUD widgets above it. Burning ~21% of screen width on infrequently-read data (DIFFICULTY) is the larger problem; enlarging the prompt inside the same cage doesn't fix it.

**Auto-grow top bar.** Bar height = whatever the longest prompt needs at a fixed point size; grid takes the rest. Rejected. Layout would shift level-to-level — the photo box stretches and shrinks across Levels, which is visually jarring during an Arc. A fixed 12% bar gives the grid a stable size.

**Multi-line wrapped prompt in a fixed bar.** Rejected for the same reason — short prompts then look like billboards while long prompts squeeze the grid further. Auto-shrink-to-fit-one-line is the simpler invariant: prompt always one line, font scales to fit.

**Hold timer in the top bar instead of overlaid on grid.** Rejected. The hold is a 1-second "doing it right" moment — it needs to be in the Player's foveal vision, which is on the grid where their body is. A widget in the top bar is peripheral when it most needs to be central.

## Consequences

- `HUD_W` is removed from `games/grid.py`. `Grid.__init__` no longer takes a `hud_width` parameter; `Grid.hud_rect`, `Grid.draw_hud_bg()`, and the HUD label/progress-bar helpers (`draw_hud_label`, `draw_progress_bar`) become unused and should be deleted.
- `games/bodycaptcha.py` `_draw_hud()` is replaced by shell rendering (top bar + hold ring + center overlays). The "DIFFICULTY" indicator is dropped from the screen — designers know it from the Level file, Players don't need it.
- `games/body_keepaway.py` migrates to the same shell. Its Levels gain an optional `prompt` field if designers want one; otherwise the bar shows only the timer.
- Shell rendering is shared across Games. Implementation choice (helper functions in `grid.py` vs. a new `games/shell.py` module vs. a `GameShell` class) is left to the implementer — the contract above is what matters.
- Future Games inherit this shell by default. Deviating (e.g. a Game without a grid at all) is allowed but should be a deliberate design choice, not an accident.
- The "select all squares" CAPTCHA mimicry reads more strongly: prompt billboard at top + image grid below is the exact reCAPTCHA shape, which is the joke FundingCAPTCHA is making.
