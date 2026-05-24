# Keepaway — game design

**Status:** Implemented as `ShowControl/FundingCAPTCHA/games/body_keepaway.py` (Body Grid input, ADR-0013).

## Concept

A chase/survival game. Players are runners — their bodies appear on a grid and must survive for a countdown timer while AI defenders hunt them. Any runner caught by a defender ends the game immediately for everyone.

The game is designed to be winnable: survive the full timer and you win.

## Input

Body Grid (`BodyGridActivator`) — per-pixel depth coverage. Every active cell is treated as a runner cell. No registration, no assignment. Walk into frame → you're playing. Walk out → you're gone. Multiple players share collective win/loss.

## Mechanics

**Win condition:** All runners survive for `survive_s` without any defender entering an occupied cell.

**Loss condition:** A defender's center enters any cell currently occupied by a runner → instant collective loss → Blow-Up.

**No runners in frame:** Timer pauses. "GET ON THE FIELD" displayed. A separate `abandon_s` (default 5s) countdown begins. If nobody re-enters before it expires → loss. Timer resumes the moment any runner cell activates.

**Defenders:** AI-controlled. Move smoothly at `speed` cells/second. Pathfind via Manhattan routing (axis-aligned only, no diagonals): at each cell arrival, move on the axis with greater remaining distance to the nearest runner cell; tie-break horizontal-first. Defenders pass through each other freely; clamp at grid edges.

**Capture:** A defender captures when its center crosses into an occupied runner cell.

**Level arc:** 5 levels, internal progression. Win a level → advance. Lose any level → reset to level 1. Final level win → `"win"` event. Loss any level → `"loss"` event.

## Level format

Levels live in `keepaway-body-levels.json` as a JSON array. Each entry:

```json
{
  "survive_s": 10,
  "defenders": [
    {"speed": 1.5}
  ],
  "grid": [8, 6],
  "grace_s": 3.0,
  "abandon_s": 5.0
}
```

`grid`, `grace_s`, and `abandon_s` are optional per-level overrides; game-wide defaults apply when absent. One object in `defenders` per AI defender — `speed` in cells/second.

### Default level arc

| Level | Defenders | Speed (cells/s) | Survive |
|-------|-----------|-----------------|---------|
| 1     | 1         | 1.5             | 10s     |
| 2     | 1         | 2.0             | 15s     |
| 3     | 2         | 2.0             | 20s     |
| 4     | 2         | 2.5             | 25s     |
| 5     | 3         | 2.5             | 30s     |

## Grace period

At the start of each level defenders spawn at their positions and freeze. A "3 … 2 … 1" countdown overlay plays for `grace_s` (default 3s). Defenders begin moving after the countdown.

**Defender spawn positions by count:**
- 1 defender → top-center cell
- 2 defenders → top-left corner, top-right corner
- 3 defenders → top-left corner, top-right corner, bottom-center cell

## Visual feedback

**Runners:** Live silhouette overlay (depth-reprojected, same as BodyCaptcha) with semi-transparent blue cell highlights on all active cells.

**Defenders:** Hand-drawn stick figures (KoL aesthetic), red, rendered at their smooth sub-cell position.

**Timer:** Countdown bar across the top of the screen, draining left-to-right, color shifting green → yellow → red.

**"GET ON THE FIELD" state:** Prompt displayed center-screen. Abandon timer shown as a separate shrinking bar.

**Win (level beat / final win):**
- Level beat → 0.5s green flash → next level loads immediately, grace countdown begins.
- Final level win → green flash across all runner cells + large "YOU SURVIVED" text displayed prominently for 2s → `DONE` state.

**Loss:**
- Current frame shatters into confetti particle animation (reuse BodyCaptcha Blow-Up).
- Random chase-themed taunt displayed (e.g. "CAUGHT!", "TAGGED!", "YOU'VE BEEN CAUGHT!").
- Animation completes → Arc ends → `DONE` state.

## Intensity signal

`intensity = clamp(w_diff × level_index/5 + w_time × elapsed/survive_s, 0.0, 1.0)`

Same formula and configurable weights as BodyCaptcha. `level_index` (1–5) is derived from internal level progression — no explicit `difficulty` field required.

## API

```python
class BodyKeepawayGame:
    def update(
        self,
        activations: CellActivations,   # from BodyGridActivator
        foreground: np.ndarray | None,  # display-space depth frame for silhouette
        dt: float
    ) -> tuple[float, str | None]:
        ...  # returns (intensity, event); event = "win" | "loss" | None

    def draw(self, surf: pygame.Surface) -> None: ...
    def reset(self) -> None: ...
```

## Config keys (`captcha-settings.json`)

```json
"keepaway_body": {
  "grid": [8, 6],
  "grace_s": 3.0,
  "abandon_s": 5.0,
  "intensity_weights": { "difficulty": 0.4, "time_pressure": 0.6 }
}
```

## Player count

Any number. All bodies in frame are runners. More players = more occupied cells = more surface area for defenders to capture = naturally harder.
