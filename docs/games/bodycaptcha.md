# BodyCaptcha — game design

**Status:** In implementation (2026-05-13). First game built on the Body Grid input layer (ADR-0013).

## Concept

A CAPTCHA-styled silhouette puzzle. A photo is displayed behind a grid overlay with a text prompt ("Select all motorcycles"). The Player must position their body so their silhouette covers exactly the correct cells — no more, no less — and hold that pose long enough to pass.

The game is designed so the Player always loses eventually. Beating a Level only escalates to a harder one. The Blow-Up is the payoff, not a failure.

## Mechanics

**Input:** Body Grid (`BodyGridActivator`) — per-pixel depth coverage. A cell is "active" when ≥ `cell_activation_threshold` of its pixels are covered by any configured Depth Slab.

**Win condition per Level:** Player covers all `valid_cells` and no non-target cells simultaneously for a continuous `hold_s` duration.
- Hold timer starts when exact match achieved.
- Hold timer resets if any extra cell is covered or any valid cell is uncovered.

**Level progression:** On beating a Level, the next Level is drawn from a shuffle-bag of Levels at the same difficulty or one step harder. No fixed ordering. No overall win — the Arc always ends when a Level's timer expires.

**Loss condition:** Level countdown timer reaches zero → Blow-Up.

## Visual feedback

| State | Valid cell | Non-valid cell |
|---|---|---|
| Not covered | Hint color at `hint_opacity` (default 10%) | Normal image |
| Covered | Bright green overlay | Red overlay (invalidates hold) |
| Hold active | Green + hold progress bar shown | — |
| Win (level beat) | Flash green | — |

## Blow-Up

On timer expiry:
1. Random taunt selected from `taunts.json` (default: "Too Slow! You're not a robot.")
2. Current Level image shatters into a confetti particle animation.
3. Animation completes → Arc ends → Screensaver.

Intentionally over-the-top and silly. Losing should feel like a payoff.

## Intensity signal

`intensity = clamp(w_diff × difficulty/5 + w_time × elapsed/timer_s, 0.0, 1.0)`

Weights `w_diff` and `w_time` are configurable in `captcha-settings.json` under `intensity_weights`.

## Level format

Levels live in `bodycaptcha-levels.json` as a JSON array:

```json
[
  {
    "prompt": "Select all motorcycles",
    "image": "motorcycles.jpg",
    "difficulty": 2,
    "grid": [4, 4],
    "valid_cells": [[0, 2], [1, 2], [2, 3]],
    "timer_s": 40,
    "hold_s": 1.0,
    "hint_opacity": 0.1
  }
]
```

`timer_s`, `hold_s`, and `hint_opacity` are optional per-Level overrides. Game-wide defaults apply when absent (see `captcha-settings.json`). `difficulty` is designer-assigned 1–5.

## Config keys (`captcha-settings.json`)

```json
"bodycaptcha": {
  "timer_s": 35,
  "hold_s": 1.0,
  "hint_opacity": 0.1,
  "intensity_weights": { "difficulty": 0.4, "time_pressure": 0.6 }
}
```

## Player count

Designed for 1–2 Players. One Player can fill cells solo; two Players cooperating can cover larger or split patterns.
