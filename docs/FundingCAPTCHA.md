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

## Maintenance mode — getting a console on the Pi

The kiosk is a systemd unit with `Restart=always` / `RestartSec=5`. Quitting the
game with **Esc** or **Q** only makes `app.py` exit; systemd relaunches it five
seconds later, forever. To actually get the machine back you have to stop the
*unit*, not the process.

### Getting a shell

**Over ethernet (easiest).** Plug in a cable, `ssh ii@captcha`, then stop the
service. No console fighting.

**On the Pi's own keyboard.** `SDL_VIDEODRIVER=kmsdrm` means pygame renders
straight to DRM and holds the tty, so VT switching usually does nothing while
the game is up. Use the restart gap instead:

1. Press **Esc** to quit the game.
2. Immediately press **Ctrl+Alt+F2** — a login prompt appears on tty2 during the
   ~5s `RestartSec` window.
3. Log in as `ii` and run `sudo systemctl stop captcha`.

**If neither works — SD card.** Mount the boot partition on another machine and
append `systemd.mask=captcha.service` to the single line in `cmdline.txt`. The
Pi then boots to a clean console every time. Remove it when you're done.

### Stop vs. disable

```bash
sudo systemctl stop captcha            # down now, back up on next boot
sudo systemctl disable --now captcha   # down now, stays down across reboots
sudo systemctl enable  --now captcha   # back to show-ready — do this before load-in
```

`stop` deactivates the unit, so `Restart=always` no longer respawns it — but the
unit is `enable`d, so a reboot brings the show straight back.

### Joining wifi from the console

```bash
sudo nmtui                                             # menu-driven, easiest at a console
sudo nmcli device wifi list
sudo nmcli device wifi connect "SSID" password "..."
ip addr show wlan0                                     # confirm an address
```

`sudo raspi-config` → System Options → Wireless LAN also works.

### Updating the game

```bash
sudo systemctl stop captcha
cd ~/CommunityGarden && git pull && git lfs pull
sudo systemctl start captcha
journalctl -u captcha -f
```

If the install uses private show content, also re-run the sync — see
[Private content sets](#private-content-sets).

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
| Game relaunches after Esc, can't get a console | `Restart=always` in `captcha.service` | Stop the unit, not the process — see [Maintenance mode](#maintenance-mode--getting-a-console-on-the-pi) |
| Need to dev away from hardware | — | `python3 app.py --test-input` — mouse paints depth (ADR-0016) |

---

## Private content sets

Some shows use artwork that cannot be published. That content lives in a
separate **private** repository, never in this one.

**Layout.** The private repo tracks its background images in Git LFS and holds
one directory per show:

```
<show-name>/levels.json
<show-name>/<background images>
```

It is cloned into `ShowControl/FundingCAPTCHA/images/private/`, which
`.gitignore` excludes. Because the clone lands inside the existing image root,
level entries reference backgrounds exactly as public levels do:

```json
{ "image": "private/<show-name>/<file>.jpg" }
```

Push the private repo to its own remote. This repo's `.gitignore` means the
public repo never contains this content, so that remote — not this one — is
the only backup and version history it gets. Images and their level
definitions are versioned together there, so a restore is a single clone and
the two can never drift apart. Skipping the push isn't optional
housekeeping: content that exists only in the working copy at
`images/private/` is content with no backup at all.

**Running a private set.**

```bash
cd ShowControl/FundingCAPTCHA
python3 app.py --camera --levels images/private/<show-name>/levels.json
```

Authoring works the same way:

```bash
cd ShowControl/FundingCAPTCHA
python3 bodycaptcha_editor.py --levels images/private/<show-name>/levels.json
```

Without `--levels`, both use `bodycaptcha-levels.json` as before. In `app.py`,
a missing or malformed file logs a warning (visible in the monitoring page's
log stream) and falls back to a single built-in default level rather than
refusing to start; a bad file discovered on a later Arc's reload logs a
warning too but keeps whatever levels are already loaded, so a half-pulled
clone mid-run does not blank the show out. The editor (`bodycaptcha_editor.py`)
falls back the same way on a bad path — a single default level, no crash — but
does not log a warning to a terminal that may not be watched. Instead, the
window title always shows the active levels path (e.g.
`BodyCaptcha Level Editor — images/private/<show-name>/levels.json`), so a
typoed `--levels` argument is visible at a glance rather than only surfacing
when a save looks wrong.

**On the show Pi.** `deploy/install.sh` can sync the private repo into
`images/private/` during install. It's entirely optional and controlled by two
environment variables, documented in `deploy/private-assets.example.env`:

- `PRIVATE_ASSETS_REPO` — SSH clone URL of the private repo.
- `PRIVATE_ASSETS_KEY` — read-only deploy key for it. Defaults to
  `<service user's home>/.ssh/private_assets_ed25519` — **not** `$HOME`,
  because `install.sh` runs under `sudo` and `$HOME` there is root's home, not
  the service user's.

To use it, copy the example file, fill in both variables, and source it before
running the installer:

```bash
cd ShowControl/FundingCAPTCHA/deploy
cp private-assets.example.env private-assets.env
# edit private-assets.env with the repo URL and key path
set -a; . ./private-assets.env; set +a
sudo -E bash install.sh
```

Leaving both variables unset skips the sync entirely and installs the default
public set — a plain `sudo bash install.sh` with no env file still works.

The sync is **non-fatal**. If the key is missing, unreadable by the service
user, or the clone/pull fails for any reason (network down, diverged history,
bad key), `install.sh` prints a loud warning and continues — it still installs
and starts the systemd unit either way. That does not mean the show comes up
on the default level set: if the systemd drop-in below already points
`--levels` at `images/private/<show-name>/levels.json`, a failed sync leaves
that path missing, and the game falls back to a single built-in placeholder
level, not `bodycaptcha-levels.json`. Check the install output (or re-run
`install.sh`) if the show is supposed to have private content but came up
looking wrong.

Once the content is on disk, point the running service at it with a systemd
drop-in rather than editing the committed unit, which stays on the default set:

```bash
sudo systemctl edit captcha
```

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 app.py --camera --port 8080 --levels images/private/<show-name>/levels.json
```

**The empty `ExecStart=` line is required.** Without it, systemd appends this
line to the committed `ExecStart=` instead of replacing it, and the unit fails
to start with both sets of arguments on one command line.

**Keeping it private.** LFS objects, once pushed, are effectively permanent —
a mistaken commit of private content into this repo cannot be undone by
amending. Two guards stop that from happening:

1. `.gitignore` excludes `ShowControl/FundingCAPTCHA/images/private/`.
2. `scripts/git-hooks/pre-commit` refuses any commit that stages a path under
   that prefix (the backstop for `git add -f`, or for a future edit that drops
   the `.gitignore` rule).

The hook is tracked in the repo but not installed by default — install it once
per clone:

```bash
bash scripts/install-git-hooks.sh
```

This symlinks the tracked hooks into `.git/hooks` (rather than setting
`core.hooksPath`, which would disable Git LFS's own hooks there).
