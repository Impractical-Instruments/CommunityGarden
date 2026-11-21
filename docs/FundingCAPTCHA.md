# FundingCAPTCHA

The 7-foot CRT-styled kiosk Element. Players activate a projected grid using their body silhouette. An **Arc** ramps difficulty until inevitable **Blow-Up**.

**Host:** `captcha` · 192.168.1.12 · **Monitor:** http://192.168.1.12:8080 · **Service:** `captcha`

Operating the kiosk (getting a console, stopping the service, updating on the Pi) is in [showtime.md](showtime.md#fundingcaptcha--getting-a-console-on-the-kiosk).

## Code

### Architecture summary

`app.py` is a single pygame process (ADR-0012) — no browser, no kiosk service. It owns the projector display, depth camera pipeline, **Game** rotation, and a monitoring server on port 8080.

`app.py` is argument parsing and wiring: it builds the pieces below and hands them to a `Kiosk`. Each is one module beside it and can be read on its own:

| Module | Its one job |
|---|---|
| `kiosk.py` | `Kiosk`: the SCREENSAVER ↔ GAME state machine (`AppState`), one tick method per state, and the one `restart()` |
| `settings.py` | Where the settings files are, the default for every key (`DEFAULTS`), how they merge, unknown-key warnings |
| `camera_feed.py` | `CameraFeed`: camera thread → foreground frames on a queue; restart; reseed. Shared with the playlist player |
| `monitor.py` | `MonitoringServer`: the port the Dashboard talks to (`/health`, `/logs`, `/api/restart`) |
| `paint_input.py` | `PaintInput`: `--test-input`, the mouse-painted foreground |
| `plugins.py` | Loads Games (`GAMES`) and screensavers from disk |
| `levels.py` | `Levels`: one levels file and its image directory — read, write, the default level, loading and cropping photos. The game and the editor are each handed one |
| `arc.py` | Runs Games as an Arc; the `Game` interface |
| `body_grid.py`, `silhouette.py` | The Body Grid activator and the silhouette drawn over the game |

State machine (no calibration screen — the depth background is learned continuously from the first frame, with people in view; ADR-0023):
- **SCREENSAVER** — idle animation; detects a Player and counts down `attract_dwell_s`
- **GAME** — active Arc; ends with a Blow-Up, returns to SCREENSAVER

Pipeline — Orbbec depth camera → IIVision self-learning background (`AdaptiveBackground`, ADR-0023) → background subtraction → despeckle → silhouette warp → **Body Grid** activator (ADR-0013). The Body Grid maps depth pixels inside configured **Depth Slabs** to a boolean grid of cells; cells go active when `≥ cell_activation_threshold` of their pixels are covered by foreground inside any slab.

Display: pygame `FULLSCREEN | NOFRAME`. Direct DRM (`SDL_VIDEODRIVER=kmsdrm`) — Pi OS Lite, no compositor.

**Games** are in `games/`; [`games/README.md`](../ShowControl/FundingCAPTCHA/games/README.md) has the modules, the `Game` interface and the rules for adding one. BodyCaptcha is the only Game loaded today. Every Game must end in a loss on its own (ADR-0003).

**Screensavers** are listed in `screensavers.json`. Today that is `ScreenSavers/pipes_3d.py`: garden-themed 3D vines. `plugins.py` (`load_screensavers`) loads them.

### `app.py` flags

| Flag | Effect |
|---|---|
| `--camera` | Real Orbbec depth camera (what the service runs) |
| `--mock-camera` | Synthetic depth frames — no hardware |
| `--test-input` | Mouse-paint depth frames (ADR-0016) for camera-free dev |
| `--test-depth MM` | Depth value (mm) painted by left-drag in `--test-input` mode |
| `--port N` | Monitoring port (default 8080) |
| `--levels PATH` | Another BodyCaptcha levels file (default `bodycaptcha-levels.json`) |

The first three are mutually exclusive. Run from `ShowControl/FundingCAPTCHA`.

Keys at runtime:
- `R` — reseed the depth background from the next frame (e.g. after moving furniture)
- `Q` / Escape — quit. Under the service, systemd starts it again 5 s later
- `C` — clear paint canvas (`--test-input` only)

### Playlist player — `playlist_app.py`

An alternative to the Game Arc: it plays Shadertoy **Setups** from `shaders/` with the depth silhouette as Buffer A (ADR-0025), and full-screen videos, in one shuffle bag. Same camera, background model and settings as `app.py`. `playlist_app.py` is the one program that plays Setups; `shader_stage.py` is the library under it (`ShaderStage`, `SetupImages`, display and camera helpers) and `video_player.py` holds the video player.

Setups in `shaders/`: `watering_can`, `endless_sunset`, `barn_dancers`, `rainbow_poop` (the shipped playlist), `logo_attract` (its interstitial), `watercolor_smudge`, `hunter_bird`, `ripples` (the example to copy) and `blob_debug` (reference reader for the tracker's **blob records**, ADR-0022). Each one's `setup.json` `_comment` says what it does; its tunables are at the top of its `common.glsl` where it has one. Writing a Setup and the channel sources: [`shaders/README.md`](../ShowControl/FundingCAPTCHA/shaders/README.md).

`playlist.json` defines the bag; every item plays once before any repeats:

- `setups`: Setup folder names from `shaders/`. Each plays for `setup_duration_s`, which overrides the Setup's own `duration_s`.
- `setup_copies`: how many times each Setup goes in the bag, so videos come round less often. Default 1.
- `videos`: file names in `ShowControl/FundingCAPTCHA/videos/`. Each plays to the end of its file, silent and letterboxed. The folder is gitignored, so copy the files onto the show machine. Decoding uses PyAV (`av`, in the `fundingcaptcha` extra of `pyproject.toml`).
- `interstitial`, `interstitial_s`: a Setup played for that long between every two items.

A missing or unreadable item is logged and skipped. The camera runs throughout, so the background keeps learning across items.

| Flag | Effect |
|---|---|
| `--camera` / `--mock-camera` | As `app.py` |
| `--test-input` | Mouse paints the Body via `shaders/body_painter.glsl`, as in Shadertoy |
| `--setup NAME` | Play one Setup alone: a one-item playlist, no cycling, no interstitial |
| `--playlist PATH` | Another playlist file (default `playlist.json`) |
| `--windowed` | 1280×720 window |
| `--display N` | Which monitor to go fullscreen on; overrides `shader_app.display` |

Keys: `N` / `→` next item · `R` reload the current Setup from disk · Escape quit.

To run it as the show, point `deploy/captcha.service`'s `ExecStart` at `playlist_app.py --camera`. `deploy/install.sh` installs the Mesa GL/EGL libraries moderngl needs. Not yet verified on the Pi 5 under `kmsdrm`; if the GL context fails to start, that is the first place to look.

### Settings — `captcha-settings.json`

Every key and its default is in `settings.py` (`DEFAULTS`), which equals the committed `captcha-settings.json`; a test keeps the two together, so change both. No other code carries a fallback value.

Per-machine overrides go in `captcha-settings.local.json` (gitignored), merged on top. Blocks merge key by key, so a local file that sets only `camera.serial` keeps the rest of `camera`; a list (`depth_slabs`) is replaced whole. A key that `DEFAULTS` does not have — a typo, or a setting nothing reads — is logged as a warning at startup. Keys starting with `_` are comments.

The keys an operator tunes:

- `depth_slabs[]` — `[{near_mm, far_mm, slab_id}, …]`: the depth range of each Play Zone. `slab_styles[<slab_id>].color` is its silhouette colour
- `camera_roi` — `{x, y, w, h}` in camera pixels: the part of the frame that maps to the screen
- `cell_activation_threshold` — fraction of a cell that must be covered to activate it
- `attract_dwell_s` — seconds a Player must dwell to leave the Screensaver
- `min_foreground_pixels` — foreground needed to count as a Player
- `silhouette_opacity`, `silhouette_dilation_px` — the silhouette overlay. Raise dilation if it looks holey; each step also fattens it by a pixel
- `detection` — `depth_delta_mm` (lower bound on the background threshold), `min_depth_mm`, `max_depth_mm`, `min_blob_pixels` (smaller regions are dropped as noise)
- `background` — the self-learning background (ADR-0023). `absorb_s` is how long before something that stopped moving becomes background; keep it above 120 for the Watering can Setup
- `bodycaptcha` — `timer_s`, `hold_s`, `hold_decay_rate`, `hint_opacity` (a Level may override any of these), and `intensity_weights`
- `camera` — `serial` (empty opens the first Orbbec found), `width`, `height`, `fps`, `pos_cm`, `rotation`
- `shader_app` — playlist player: `render_scale`, `display`, `fps`, and `blobs` (blob-record tracking, ADR-0022)

### Level assets

Files beside `app.py`:
- `bodycaptcha-levels.json` — BodyCaptcha Levels (prompt, background, `grid`, `valid_cells`, `difficulty`, optional `timer_s`/`hold_s`/`hold_decay_rate`/`hint_opacity`/`crop_align`)
- `taunts.json` — per-Arc taunt strings
- `images/` — Level background photos (`.jpg` and `.png` are Git LFS)

Level photos are drawn into the grid bounds, whose aspect is `cols/rows`. A photo of any other aspect is **cropped** to fit, never squashed. Optional `crop_align` picks which part survives the crop — one of `top-left`, `top`, `top-right`, `left`, `center`, `right`, `bottom-left`, `bottom`, `bottom-right`; omitted means `center`.

A missing or malformed levels file at startup logs a warning and the game runs one built-in default level. A bad file found on a later reload keeps the levels already loaded.

**Level editor.** `python3 bodycaptcha_editor.py`, or on macOS double-click `BodyCaptchaEditor.command`. `--levels PATH` edits another file; the window title always shows which. Its CROP ALIGN pad previews the framing the show will render. The code is `bodycaptcha_editor.py` (window, event loop) and `editor/` (`level_model.py`, `views.py`, `widgets.py`, `theme.py`); file reading and writing is `levels.py`, shared with the game.

### OSC Fabric output

FundingCAPTCHA sends two signals to the TreeHouse and receives none. Arguments: [`osc-fabric.md`](osc-fabric.md).

| Address | Meaning |
|---|---|
| `/captcha/intensity` | Arc progress toward Blow-Up: a weighted sum (`bodycaptcha.intensity_weights`) of difficulty and time pressure. 0 whenever no Arc is running. Sent when it changes and again on the Fabric heartbeat, in both states; during a Game a change goes out at most every 0.1 s (`OSC_INTERVAL_S` in `kiosk.py`) |
| `/captcha/blowup` | Sent once when an Arc ends in a Blow-Up |

`Kiosk.tick()` calls `FabricClient.tick(dt)` every frame, so intensity is sent again every `heartbeat_interval_s` (`network.json`) even when it has not changed: 0 through the Screensaver, the Game's value during an Arc. When an Arc ends, with or without a Blow-Up, the kiosk reports 0 in the same frame, after `/captcha/blowup` if there is one. Not yet watched on the TreeHouse hardware.

### Monitoring server

`monitor.py`, on `--port` (8080). It serves JSON and a log socket; there is no HTML page. The Dashboard's FundingCAPTCHA page is the reader.

| Path | What it does |
|---|---|
| `GET /health` (or `/`) | The last status: `{"state": "screensaver" \| "game", "fg_pixels": N}`, or `{"state": "error", "error": …}` when the camera has failed |
| `WS /logs` | Every log record as `{"ts", "level", "msg"}` |
| `/api/restart` | Back to a clean Screensaver; the camera restarts and relearns its background |

## Operations

For whoever is running the Element at a show. A code change rarely needs it.

### Service unit notes

`deploy/captcha.service` (placeholders filled in by `deploy/install.sh`):
- `ExecStart=/usr/bin/python3 app.py --camera --port 8080`, `Restart=always`, `RestartSec=5`
- `Environment=SDL_VIDEODRIVER=kmsdrm` (Pi OS Lite, no compositor — direct DRM)
- `Environment=XDG_RUNTIME_DIR=/run/user/<uid of the service user>`
- `SupplementaryGroups=video plugdev render` (camera + DRM)
- `After=network-online.target graphical.target`

`install.sh` also writes the Orbbec udev rule and pulls the Git LFS images.

### Private content sets

Some shows use artwork that cannot be published. It lives in a separate **private** repository, cloned into `ShowControl/FundingCAPTCHA/images/private/`, with one directory per show holding a `levels.json` and its images. A level there references a background as `private/<show-name>/<file>.jpg`.

**The rule (AGENTS.md constraint 5):** never commit anything under `images/private/`, and never write a show, artist or album name into any file in this repo. `.gitignore` excludes the directory and the pre-commit hook (installed by `make setup`) refuses a commit that stages a path under it. The private repo's own remote is that content's only backup: push it.

**Run or edit a private set:**

```bash
cd ShowControl/FundingCAPTCHA
python3 app.py --camera --levels images/private/<show-name>/levels.json
python3 bodycaptcha_editor.py --levels images/private/<show-name>/levels.json
```

**On the show Pi,** `deploy/install.sh` clones or pulls the private repo when two environment variables are set (`deploy/private-assets.example.env` documents them):

- `PRIVATE_ASSETS_REPO` — SSH clone URL of the private repo. Unset: the sync is skipped.
- `PRIVATE_ASSETS_KEY` — read-only deploy key. Defaults to `.ssh/private_assets_ed25519` in the service user's home, not root's.

```bash
cd ShowControl/FundingCAPTCHA/deploy
cp private-assets.example.env private-assets.env     # fill in both; never commit the copy
set -a; . ./private-assets.env; set +a
sudo -E bash install.sh
```

A failed sync prints a warning and the install carries on. Then point the service at the set with a drop-in (`sudo systemctl edit captcha`), not by editing the committed unit. The empty `ExecStart=` line is required, or systemd appends instead of replacing:

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 app.py --camera --port 8080 --levels images/private/<show-name>/levels.json
```

If the show comes up on a single placeholder level, the drop-in points at a file the sync did not deliver: read the install output and run it again.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No silhouette ever appears | Camera not producing frames | Check Orbbec USB; check udev rule (`install.sh` writes it — re-run if missing); `journalctl -u captcha -f` |
| Players ignored, screensaver loops | `min_foreground_pixels` too high, or slab depths wrong | Tune `depth_slabs[]` near/far per Play Zone |
| A ghost silhouette that won't go away, or a still Player fading out | Something moved into the scene (absorbed after `background.absorb_s`), or a Player stood still longer than that | Wait it out, or press `R` to reseed the background; tune `background.absorb_s` (keep > 120) |
| Cells flicker on/off | `cell_activation_threshold` too low | Raise it (try 0.40) |
| Game never escalates | Level set thin or shuffle bag favoring easy | Add Levels at higher `difficulty`; check `intensity_weights` |
| Game refuses to end | Game lacks self-termination | Audit Game code against ADR-0003 |
| Silhouette does not line up with the Players | `camera_roi`, or `camera.pos_cm` / `camera.rotation`, no longer match where the camera is mounted | Correct them in `captcha-settings.local.json` |
| Game relaunches after Esc, can't get a console | `Restart=always` in `captcha.service` | Stop the unit, not the process — see [showtime.md](showtime.md#fundingcaptcha--getting-a-console-on-the-kiosk) |
| Need to dev away from hardware | — | `uv run python app.py --test-input` — mouse paints depth (ADR-0016) |
