# FundingCAPTCHA runs as a unified pygame app

The FundingCAPTCHA show computer runs a single Python process (`app.py`) that owns the projector display, the camera pipeline, and a lightweight monitoring server. There is no browser, no kiosk service, and no separate calibration tool.

## Context

The previous architecture split responsibilities across three processes:

1. `server.py` — FastAPI server: served browser games over HTTP, relayed blob data via WebSocket, handled photo uploads, ran the IIVision camera pipeline
2. `captcha-kiosk.service` — cage + Chromium in kiosk mode, pointing at `localhost:8080`
3. `touch_calibration.py` — standalone pygame tool that connected to `server.py` via WebSocket and displayed calibration UI on the projector

This split created coordination problems:

- **Calibration timing**: the calibration tool had no way to tell the server to blank the projector during background capture; this caused background model corruption from laser projector IR interference (see ADR-0004).
- **State coupling**: the kiosk browser and the calibration tool both rendered to the same display but ran as separate processes, requiring careful startup ordering.
- **Complexity**: three independent failure modes, two systemd services, a cage/Chromium layer, and a WebSocket round-trip for blob data the calibration tool needed locally.

## Decision

A single pygame process (`app.py`) replaces all three:

```
app.py
├── CameraThread         — IIVision pipeline (blob detection, stabilisation)
├── AppStateMachine      — BG_CAL → CORNER_CAL → LIVE → (game rotation)
├── PygameRenderer       — fullscreen display; black during BG_CAL
└── MonitoringServer     — asyncio HTTP/WS on port 8080
    ├── GET  /           → monitoring status JSON
    ├── WS   /ws         → pushes blobs, touch state, game state, logs
    ├── WS   /logs       → log stream (for dashboard)
    └── POST /api/restart → trigger recalibration
```

**Games** are native pygame modules in `games/` (UpsideDown, Rhythm, Keepaway). The browser JS game stack is deleted.

**Photo management**: photos live in `images/`. Each game has its own config file (`pairs.json` for UpsideDown, `rhythm-images.json`, `keepaway-images.json`). All configs default to `[]`; games fall back to text/emoji when empty. No upload endpoint.

**Pairing**: `pairs.json` is the config file for matching photo pairs (UpsideDown). Format: `[{"label": "str", "a": "file_a.jpg", "b": "file_b.jpg"}]`. Edited locally.

**Monitoring**: the dashboard (`Dashboard/fundingcaptcha.html`) connects to the monitoring WebSocket for logs and touch debug visualisation. It no longer embeds the game as an iframe.

## Consequences

- One systemd service (`captcha.service`) replaces two (`captcha.service` + `captcha-kiosk.service`).
- The projector display is always owned by `app.py`; black-screen during BG_CAL is guaranteed (see ADR-0004).
- Browser game files (`index.html`, `main.js`, `grid.js`, `blob-ws.js`, `touch-input.js`, etc.) and JS game modules (`games/upsidedown.js`, `rhythm.js`, `keepaway.js`) are deleted. ✓
- `server.py` and `touch_calibration.py` are deleted. ✓
- `deploy/captcha-kiosk.service` is deleted; `deploy/install.sh` updated accordingly. ✓
- The monitoring WebSocket is lightweight (no FastAPI dependency for the game path); FastAPI is replaced by a plain asyncio HTTP/WS server.
- `screen_rect` is removed from `captcha-settings.json` (was browser-only; see ADR-0011).
- Photo upload endpoint (`POST /upload`, `GET /api/photos`) is removed. Photos live in `images/` and are managed locally.
- Gallery and pairing workflow (`gallery.html`, `upload.html`) are removed; pairings are configured directly in `pairs.json`.
