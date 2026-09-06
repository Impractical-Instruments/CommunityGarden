# FundingCAPTCHA

The 7-foot CRT-styled kiosk Element. Players activate a projected grid using their body silhouette. An **Arc** ramps difficulty until inevitable **Blow-Up**.

**Host:** `captcha` · 192.168.1.12 · **Monitor:** http://192.168.1.12:8080 · **Service:** `captcha`

---

## Architecture summary

`app.py` is a single pygame process (ADR-0012) — no browser, no kiosk service. It owns the projector display, depth camera pipeline, BG calibration, **Game** rotation, and a lightweight HTTP/WebSocket monitoring server on port 8080.

State machine:
- **BG_CAL** — solid black; depth camera builds a `calibration_frames` background model
- **SCREENSAVER** — idle animation; detects a Player and counts down `attract_dwell_s`
- **GAME** — active Arc; ends with a Blow-Up, returns to SCREENSAVER

Pipeline — Orbbec depth camera → IIVision background subtraction → silhouette warp → **Body Grid** activator (ADR-0013). The Body Grid maps depth pixels inside configured **Depth Slabs** to a boolean grid of cells; cells go active when `≥ cell_activation_threshold` of their pixels are covered by foreground inside any slab.

Display: pygame `FULLSCREEN | NOFRAME`. Direct DRM (`SDL_VIDEODRIVER=kmsdrm`) — Pi OS Lite, no compositor (ADR-0011).

Games are loaded from `games/` (one module each). Game scheduling is a shuffle bag — every Game plays in random order before any repeats. Per-game **Levels** come from JSON files alongside `app.py`. The Arc ends on timer expiry or Game-defined Blow-Up condition (ADR-0003 — every Game must guarantee a loss).

Key references:
- ADR-0003 — Games must self-terminate
- ADR-0004 — depth-only touch detection
- ADR-0011 — screen calibration + projection
- ADR-0012 — unified pygame app
- ADR-0013 — silhouette body interaction
- ADR-0016 — `--test-input` mouse-paint dev mode
- ADR-0019 — game UI shell
- `app.py`, `body_grid.py`, `silhouette.py`, `games/`, `ScreenSavers/`

---

## `app.py` flags

| Flag | Effect |
|---|---|
| `--camera` | Real Orbbec depth camera (default for service) |
| `--mock-camera` | Synthetic depth frames — no hardware |
| `--test-input` | Mouse-paint depth frames (ADR-0016) for camera-free dev |
| `--test-depth MM` | Depth value (mm) painted by left-drag in `--test-input` mode |
| `--port N` | Monitoring HTTP/WebSocket port (default 8080) |

The first three are mutually exclusive.

Keys at runtime:
- `R` — restart from BG_CAL
- `Q` / Escape — quit
- `C` — clear paint canvas (`--test-input` only)

---

## Settings — `captcha-settings.json`

Per-machine overrides go in `captcha-settings.local.json` (loaded second, shallow-merged on top — not gitignored, but per-host).

Top-level fields:
- `camera` — Orbbec config (`serial`, `width`, `height`, `fps`, `pos_cm`, `rotation`)
- `detection` — `depth_delta_mm`, `min_blob_pixels`, `min_depth_mm`, `max_depth_mm`
- `depth_slabs[]` — `[{near_mm, far_mm, slab_id}, …]`; two slabs may share `slab_id`
- `slab_styles[<slab_id>]` — `{color}` for silhouette render
- `cell_activation_threshold` — fraction of cell coverage required (default 0.30)
- `camera_roi` — `{x, y, w, h}` in camera pixel coords
- `attract_dwell_s` — seconds a Player must dwell to exit Screensaver
- `min_foreground_pixels` — anti-noise threshold for Player presence
- `silhouette_opacity` — 0–1, silhouette overlay opacity in-game
- `calibration_frames` — default 60
- Per-game blocks: `bodycaptcha`, `keepaway_body` (timer_s, grace_s, abandon_s, weights for **Intensity** computation)

---

## Level assets (per-game JSON)

Files live alongside `app.py`:
- `bodycaptcha-levels.json` — BodyCaptcha Levels (prompt, background, `grid`, `valid_cells`, `difficulty`, optional `timer_s`/`hold_s`/`hint_opacity`/`crop_align`)
- `keepaway-body-levels.json` — Keepaway Levels
- `taunts.json`, `keepaway-body-taunts.json` — per-Arc taunt strings
- `screensavers.json` — list of screensaver modules to load
- `images/` — Level background photos

Level photos are drawn into the grid bounds, whose aspect is `cols/rows`. A photo
of any other aspect is **cropped** to fit, never squashed. Optional `crop_align`
picks which part survives the crop — one of `top-left`, `top`, `top-right`,
`left`, `center`, `right`, `bottom-left`, `bottom`, `bottom-right`; omitted means
`center`. The level editor's CROP ALIGN pad sets it, previewing the exact framing
the show will render.

A standalone Windows level editor for non-git teammates lives in `distribution/` (build with `distribution/build.py`; see `distribution/README.md`). Edited level packs come back in zip form; `distribution/merge_levels.py` merges them into the canonical JSON.

---

## Games (`games/`)

| Module | Game | Notes |
|---|---|---|
| `bodycaptcha.py` | **BodyCaptcha** | Match the prompt by activating the right grid cells |
| `body_keepaway.py` | **Keepaway** | **Not loaded** — the kiosk plays BodyCaptcha only. Module and its Level/taunt data retained for a future return |
| `grid.py` | shared overlay | Cell boundary drawing, used by all Games |

Every Game must guarantee a loss after sustained inactivity (ADR-0003) — either via the Level timer, or via mechanics that ensure failure without Player input.

---

## Screensavers (`ScreenSavers/`)

Loaded from `screensavers.json`. Currently — `pipes_3d.py` (Windows-style 3D pipes screensaver), `waiting.py` (idle waiting). Add new ones by dropping a module exposing `create(settings) -> Screensaver` and listing it in `screensavers.json`.

---

## OSC Fabric output

FundingCAPTCHA sends to the TreeHouse Hub each frame:

| Address | Args | Meaning |
|---|---|---|
| `/captcha/intensity` | `f 0–1` | Arc progress toward Blow-Up. Configurable weighted sum of difficulty (current Level / 5) and time pressure (elapsed / `timer_s`). Resets to 0 at the start of each Arc. |
| `/captcha/blowup` | — | One-shot — sent on the frame a Blow-Up fires. TreeHouse responds with the **Blow-Up Reaction** (attic spike + exponential decay). |
| `/captcha/mode` | `s` (in) | `active` / `dim` / `inactive` from Dashboard |

---

## Monitoring server

`http://<host>:8080/` — small HTML page with state + live log stream over WebSocket. Includes:
- Current `AppState` (BG_CAL / SCREENSAVER / GAME)
- Current Game + Level
- Live `intensity` value
- Last 100 log lines

Logs stream over a separate WebSocket; `_LogHandler` in `app.py` pumps records to connected clients.

---

## Service unit notes

`captcha.service`:
- `Environment=SDL_VIDEODRIVER=kmsdrm` (Pi OS Lite, no compositor — direct DRM)
- `Environment=XDG_RUNTIME_DIR=/run/user/1000`
- `SupplementaryGroups=video plugdev render` (camera + DRM)
- `After=network-online.target graphical.target` (graphical.target so DRM is available)

`install.sh` writes the Orbbec udev rule itself — no manual rule needed.

---

## Body Grid tester

`body_grid_tester.py` — standalone tool to exercise the Body Grid in isolation (no Game). Useful for verifying camera calibration + slab config visually.

```bash
cd ShowControl/FundingCAPTCHA
python3 body_grid_tester.py
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Black screen, stuck in BG_CAL | Camera not producing frames | Check Orbbec USB; check udev rule (`install.sh` writes it — re-run if missing); `journalctl -u captcha -f` |
| Players ignored, screensaver loops | `min_foreground_pixels` too high, or slab depths wrong | Body grid tester; tune `depth_slabs[]` near/far per Play Zone |
| Cells flicker on/off | `cell_activation_threshold` too low | Raise it (try 0.40) |
| Game never escalates | Level set thin or shuffle bag favoring easy | Add Levels at higher `difficulty`; check `intensity_weights` |
| Game refuses to end | Game lacks self-termination | Audit Game code against ADR-0003 |
| Projector misaligned | Calibration drift | Re-do screen calibration per ADR-0011 |
| Need to dev away from hardware | — | `python3 app.py --test-input` — mouse paints depth (ADR-0016) |
