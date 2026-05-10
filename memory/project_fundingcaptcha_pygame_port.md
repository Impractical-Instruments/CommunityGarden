---
name: FundingCAPTCHA unified pygame app
description: Architecture and status of FundingCAPTCHA rewrite — unified pygame app replacing browser+server split
type: project
---

All three games (UpsideDown, Rhythm, Keepaway) being ported to pygame as part of a unified app.

**Why:** Browser kiosk (server.py + Chromium + touch_calibration.py) split made calibration coordination impossible — projector on during BG_CAL corrupted background model, causing misses. Unified pygame app owns display and can black screen during calibration.

**Architecture (ADR-0012):**
- `app.py` = single process: camera + calibration + game + monitoring WS
- Replaces: `server.py`, `touch_calibration.py`, `captcha-kiosk.service`
- Monitoring WS on port 8080 (logs + blob data for dashboard)
- No browser, no upload endpoint

**Touch fixes (ADR-0004):**
- `fg_from_invalid` removed from `blob_tracker.py` (depth dropouts ≠ foreground)
- `depth_delta_mm`: 10 → 25 in `captcha-settings.json`
- `app.py` blacks screen during BG_CAL (projector off = clean depth background)
- IR amplitude masking deferred — validate simpler fixes first

**Photo management:** git LFS in `uploads/`, `pairs.json` local config. No upload endpoint.

**Status (2026-05-10):** Docs updated. Code not yet written. Next: implement `app.py` + three pygame games + blob_tracker.py fix + settings update.

**How to apply:** When working on FundingCAPTCHA touch/calibration, context is depth-primary detection with black-screen calibration. When working on game code, target pygame not browser. `server.py` and `touch_calibration.py` are slated for deletion.
