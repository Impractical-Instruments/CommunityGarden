# FundingCAPTCHA games use pygame instead of a browser kiosk

The game display layer was originally a browser application (Chromium in kiosk mode via cage/Wayland compositor) served by a FastAPI server. The browser stack was fragile on Raspberry Pi — cage, Chromium, and the readiness-check startup sequence added failure modes with no recovery path.

## Decision

Replace the browser game layer with a pygame application (`captcha.py`). The FastAPI server (`server.py`) is retained for blob WebSocket streaming, OSC relay, and organiser tools (upload.html, gallery.html). The pygame client connects to the server's existing `/ws` WebSocket for blob input and POSTs to `/api/game-event` for OSC relay, exactly as the browser did.

## Architecture

**Background rendering:** `background.py` uses moderngl (OpenGL 3.3) to render per-game GLSL fragment shaders behind the game UI. The pygame game surface is composited over the shader as a texture each frame (hybrid approach: shader background + pygame surface overlay). Falls back to solid-color fill if moderngl is unavailable.

**Touch input:** `touch_input.py` wraps `ScreenProjector` and `DwellTracker` from `touch_calibration.py`. Consumes blob JSON from the server WebSocket; fires `on_tap(col, row)` callbacks on dwell completion. Screen corner calibration (`touch_calibration.py`) is unchanged.

**Dev modes:**
- `python captcha.py` — mouse clicks map to grid taps (no server required)
- `python captcha.py --mock-camera` — blobs from server mock-camera WebSocket
- `python captcha.py --camera` — blobs from server real-camera WebSocket

**Deployment:** `captcha-pygame.service` replaces `captcha-kiosk.service`. Launches pygame under X11 (`DISPLAY=:0`); waits for server `/health` before starting.

## Game port order

1. UpsideDown (`games/upsidedown.py`) — memory match, no audio, proves full stack
2. Rhythm (`games/rhythm.py`) — adds numpy/pygame triangle-wave audio synth
3. Keepaway (`games/keepaway.py`) — adds AI defenders and real-time movement

## Consequences

- `captcha-kiosk.service`, `cage`, and Chromium are no longer needed on the kiosk Pi.
- Browser game files (`index.html`, `main.js`, `grid.js`, `touch-input.js`, `blob-ws.js`, `background-renderer.js`, `style.css`, `games/*.js`) are deleted after each pygame game is verified working.
- `screen_rect` in `captcha-settings.json` is now unused and can be deleted.
- `GET /api/captcha-settings` endpoint is removed from `server.py` (pygame reads the file directly).
- Organiser browser tools (upload.html, gallery.html) remain browser-based, served by FastAPI.
