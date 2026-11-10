# FundingCAPTCHA audit — `ShowControl/FundingCAPTCHA/`

Read-only analysis, 2026-11-09. All paths are relative to `ShowControl/FundingCAPTCHA/` unless prefixed. `images/private/` does not exist in this checkout and was not listed.

Goal lens: small files, isolated reasoning, no dead code, no stale docs.

---

## 0. Headline

- **10,992 LOC Python** (5,580 source / 5,412 tests), 3,257 LOC GLSL, 428 lines JSON.
- The directory is really **three products sharing one folder**: (a) the BodyCaptcha kiosk (`app.py` + `games/` + `arc.py` + `body_grid.py`), (b) the shader player (`shader_app.py`, `playlist_app.py`, `shadertoy.py`, `body_blobs.py`, `shaders/`), (c) the level-authoring toolchain (`bodycaptcha_editor.py`, `crop.py`, `distribution/`, `BodyCaptchaEditor.command`). Plus one orphaned dev tool (`body_grid_tester.py`).
- **Confirmed dead**: `games/body_keepaway.py` (498 LOC, never loaded: `app.py:349-351`), ~45 LOC in `games/grid.py`, `ScreenSavers/waiting.py` (stub superseded by `pipes_3d`), 16 of 24 LFS images under `images/yeavl_may/`, `distribution/` (297 LOC, no commits since May, superseded for Mac by the `.command`, Windows build never re-shipped).
- **Live bug**: `app.py:551` `_save_local({})` overwrites `captcha-settings.local.json` with `{}` on every `R` keypress / `/api/restart`, wiping per-host overrides. Leftover from the corner-cal era (ADR-0012), never removed when ADR-0013 deleted CORNER_CAL.
- **Biggest duplication**: camera thread + monitoring server + settings loader exist twice (`app.py` vs `body_grid_tester.py`, ~160 LOC verbatim-ish), and the shader behaviour tests reimplement a GL test rig **five times** (~350 LOC of copy-pasted fixtures/helpers).
- **Docs**: `docs/FundingCAPTCHA.md` describes a monitoring HTML page, an inbound `/captcha/mode` OSC address, and a non-gitignored local settings file — none exist. `docs/games/*.md` and ADR-0012/0013 describe pre-ADR-0019 UI and pre-#150 hold mechanics. CONTEXT.md still says `app.py` "loads all Games" including UpsideDown/Rhythm/Keepaway.
- **Estimated deletable now**: ~1,500 LOC (conservative, keeps tester and editor); ~2,100 if `body_grid_tester.py` is folded into `app.py --tester` and `distribution/` is removed.

---

## 1. Inventory

### Entry points

| File | LOC | Classification | Evidence |
|---|---|---|---|
| `app.py` | 756 | **Production show path** | `deploy/captcha.service:11` `ExecStart=… app.py --camera --port 8080` |
| `shader_app.py` | 370 | **Production (alternate show mode)** + library for `playlist_app` | docs/FundingCAPTCHA.md:74 "point ExecStart at shader_app.py"; `playlist_app.py:35-36` imports 6 names from it |
| `playlist_app.py` | 421 | **Production (alternate show mode)**, newest (#169, 2026-11-08) | imports `app.load_settings`, `shader_app.*`; supersedes `shader_app.main()` as the richer rotation (Setups + videos) |
| `body_grid_tester.py` | 626 | **Dev-only tool / near-abandoned** | 3 commits (2026-05-12 → 2026-09-06; the last is a search-replace in #150). Own copies of settings loader, monitoring server, camera thread. Reads config keys (`grid`, `activation_rule`) that exist in no settings file. |
| `bodycaptcha_editor.py` | 847 | **Operator / content-author tool** | `BodyCaptchaEditor.command` (macOS launcher, #152 2026-09-30); `docs/FundingCAPTCHA.md:313` |
| `ScreenSavers/pipes_3d.py` | 412 | Production (screensaver) + has own `__main__` preview (`:427-454`) | listed in `screensavers.json` |
| `ScreenSavers/waiting.py` | 42 | Production but **stub** ("Stub screensaver … Replace with generative visuals", `:1`) | listed in `screensavers.json` |
| `distribution/build.py` | 67 | **Dev-only / probably abandoned** | PyInstaller Windows build; the three scripts were created in one commit (#94, 2026-05-23) and never changed; only `distribution/README.md` was touched since (#152, 2026-09-30, adding the Mac run-from-source path). `dist/` gitignored. README says re-run after every editor change — editor changed 3× in Sept (#143–#145) with no rebuild trail. |
| `distribution/package.py` | 101 | same | |
| `distribution/merge_levels.py` | 129 | **Operator tool / probably abandoned** | no tests; only referenced from `distribution/README.md` and `docs/FundingCAPTCHA.md:128` |

### Library modules

| File | LOC | Purpose | Imported by |
|---|---|---|---|
| `arc.py` | 129 | `Arc`, `ArcStatus`, `Game` interface, `_NoGame`, `ShuffleBag`, `blend_intensity` | `app.py:47`, `shader_app.py:38`, `playlist_app.py:34`, `games/bodycaptcha.py:24`, `games/body_keepaway.py:23`, `test_arc.py` |
| `body_grid.py` | 97 | `BodyGridActivator`: foreground depth frame → `{(col,row): [(slab_id, coverage)]}` | `games/bodycaptcha.py:22`, `games/body_keepaway.py:21`, `body_grid_tester.py:56`, `test_body_grid.py` |
| `silhouette.py` | 76 | `render_silhouette`, `build_cam_transform`, `apply_cam_transform` | `app.py:46`, `body_grid_tester.py:57`, `games/bodycaptcha.py:23`, `games/body_keepaway.py:22`, `test_silhouette.py` |
| `crop.py` | 62 | `crop_rect`, `crop_scale`, `ANCHORS` — aspect-preserving crop | `bodycaptcha_editor.py:12`, `games/bodycaptcha.py:25`, `test_crop.py` |
| `shadertoy.py` | 468 | Shadertoy-compatible multipass GL renderer: `load_setup`, `wrap_source`, `pack_body`, `BodyMouse`, `Keyboard`, `js_keycode`, `Renderer`, `_PingPong`, BLOB_* constants | `shader_app.py:40`, `playlist_app.py:37`, `body_blobs.py:31`, 7 test files |
| `body_blobs.py` | 207 | `BodyBlobs`/`BlobConfig`/`find_blobs`: connected components + `IIVision.BlobStabilizer` → 8×3 record texture | `shader_app.py:39`, `test_body_blobs.py`, `test_hunter_bird.py`, `test_watering_can.py`, `test_rainbow_poop.py` |
| `games/grid.py` | 258 | `Grid` letterbox geometry + ADR-0019 shell renderers (`draw_top_bar`, `draw_hold_ring`, `draw_center_text`) + font caches + colour constants | `games/bodycaptcha.py:16`, `games/body_keepaway.py:16` |
| `games/bodycaptcha.py` | 477 | BodyCaptcha Game: level bag, hold/drain, blow-up confetti, drawing, hot-reload, `--levels` override | `app.py:357` (importlib, by filename), 5 test files |
| `games/body_keepaway.py` | 498 | Keepaway Game (4 commits, 2026-05-22 #90 → 2026-06-04; unplugged from the Arc in #142, 2026-09-06) | **nothing** (see §2) |

### Tests (5,412 LOC)

| File | LOC | Tests | Needs GL |
|---|---|---|---|
| `test_watering_can.py` | 1097 | shader `watering_can` behaviour | yes |
| `test_hunter_bird.py` | 667 | shader `hunter_bird` behaviour | yes |
| `test_endless_sunset.py` | 601 | shader `endless_sunset` behaviour | yes |
| `test_shadertoy.py` | 465 | `shadertoy.py` + `shader_app.Rotation` + blob painter | partly |
| `test_rainbow_poop.py` | 439 | shader `rainbow_poop` behaviour | yes |
| `test_bodycaptcha_editor.py` | 218 | editor crop/align/levels path | no (SDL dummy) |
| `test_playlist_app.py` | 203 | playlist + video decode | yes + `av` |
| `test_body_grid.py` | 179 | activator | no |
| `test_bodycaptcha_levels.py` | 177 | levels I/O + override | no |
| `test_bodycaptcha_hold.py` | 151 | hold/drain | no |
| `test_body_blobs.py` | 148 | tracker records | no |
| `test_crop.py` | 132 | crop geometry | no |
| `test_silhouette.py` | 129 | render + reproject | no |
| `test_arc.py` | 117 | Arc/ShuffleBag/blend | no |
| `ScreenSavers/test_pipes_3d.py` | 98 | vines smoke | no |
| `test_bodycaptcha_bg.py` | 77 | bg crop | no |
| `test_app_games.py` | 51 | `_load_games` | no |

### Data / assets

| Path | Status |
|---|---|
| `captcha-settings.json` (74) | live, read by `app.py`, `shader_app.py`, `playlist_app.py`, `body_grid_tester.py`, games |
| `bodycaptcha-levels.json` (230, 9 levels) | live |
| `taunts.json` (27) | live (`games/bodycaptcha.py:289`) |
| `keepaway-body-levels.json`, `keepaway-body-taunts.json` | read only by dead `body_keepaway.py` |
| `screensavers.json` | live (`app.py:382`) |
| `playlist.json` | live (`playlist_app.py:41`) |
| `shaders/setups.json` | live (`shader_app.py:149`, `test_shadertoy.py:179`) |
| `shaders/{ripples,endless_sunset,hunter_bird,watering_can,rainbow_poop}/` | all in rotation |
| `shaders/blob_debug/` | reference reader, not in rotation (intentional, `setup.json:_comment`) |
| `shaders/body_painter.glsl`, `blob_painter.glsl` | live (`shadertoy.py:51-52`) |
| `images/jess.jpg` + 8 of `images/yeavl_may/*.jpg` | referenced by levels |
| **16 other `images/yeavl_may/*.jpg`** | **unreferenced** (24 files in dir, 8 referenced) — LFS blobs, ~1 commit each in May |
| `videos/` | gitignored, README only |
| `deploy/` | live |
| `BodyCaptchaEditor.command` | live (macOS) |

---

## 2. Dead code

Verified by grep over the whole repo (`the repo root`), not just this directory.

### Whole files / directories

1. **`games/body_keepaway.py` (498 LOC)** + `keepaway-body-levels.json` (22) + `keepaway-body-taunts.json` (17) + `captcha-settings.json:44-49` `keepaway_body` block. `app.py:349-351` hardcodes `for name in ("bodycaptcha",)`. `test_app_games.py:26-28` asserts Keepaway is *not* loaded. Nothing else imports the module. "Retained for a future return" (app.py:349) — git history is the retention mechanism; this is ~540 LOC the Arc never reaches, which every reader of `games/` still has to rule out.
2. **`ScreenSavers/waiting.py` (42 LOC)**. Self-described stub. `pipes_3d.py:382-402` already draws the identical title + "Step into frame to begin" overlay. Having both in `screensavers.json` means 50% of idle time is the stub. Delete and drop from `screensavers.json`.
3. **`distribution/` (297 LOC Python + ~150 lines of README/TXT)**. Evidence of abandonment: all three scripts date from one commit (#94, 2026-05-23) and have never been edited; the editor had 3 substantive changes in Sept (#143, #144, #145) with no rebuild/resend trail; `BodyCaptchaEditor.command` (#152) is the newer teammate path and `distribution/README.md:30-36` says Mac users "commit on a branch instead of using the zip/merge flow". `merge_levels.py` has no tests. The `sys.frozen` branch in `bodycaptcha_editor.py:16-19` exists only for this. **Confirm with the owner**; if no Windows teammate is active, delete the directory and the frozen-path branch.
4. **16 unreferenced images in `images/yeavl_may/`**. `bodycaptcha-levels.json` references `jess.jpg` + 8 yeavl_may files; the directory holds 24. All images landed 2026-05-10 → 2026-05-30 (3 commits) and none has been referenced since. These are LFS objects pulled on every Pi install (`deploy/install.sh:30`).

### Dead members inside live files

| Location | What | Why dead |
|---|---|---|
| `app.py:90-91`, `:551` | `_save_local()` and its one call | Writes `{}` to `captcha-settings.local.json`. Nothing reads it back except `load_settings` on next boot — so this **destroys per-host overrides**. Leftover from corner-cal persistence (ADR-0012 era). Bug, not just dead. |
| `app.py:69-73` | `MID_GREY`, `LT_GREY`, `GREEN`, `YELLOW`, `RED` | `app.py` uses only `BLACK`, `WHITE`, `DK_GREY`, `CYAN` |
| `app.py:284-285` | `# ── Silhouette rendering ──` empty section header | leftover from `bf83c47` extraction |
| `app.py:104,133-149,152-163,189-194` | `/ws` status WebSocket + `broadcast()` + `_app_status` | Only consumer is `Dashboard/index.html:78` which polls `GET /health`. Nothing connects to `/ws` (`Dashboard/fundingcaptcha.html:49` uses `/logs` only; `index.html` uses HTTP). `broadcast()` is called 9× per loop iteration for no listener. Keep `/health` JSON; delete the `/ws` channel or find a client. |
| `games/grid.py:18-24` | `SUCCESS_COLOR`…`HIGHLIGHT_COLOR` (7 aliases) | zero references outside grid.py |
| `games/grid.py:26,90-91` | `CELL_PAD`, `Grid.inner_rect` | only used by `blit_cell` (dead) |
| `games/grid.py:67,93-115` | `Grid._flashes`, `Grid.flash()`, `Grid.draw_flashes()` | zero callers |
| `games/grid.py:97-102` | `Grid.draw_background()` | zero callers (both games draw cells inline) |
| `games/grid.py:117-120` | `Grid.blit_cell()` | zero callers |
| `games/grid.py:16` | `BLUE` | imported by `body_keepaway.py:18` but unused there (it defines `RUNNER_COLOR` locally) |
| `games/body_keepaway.py:19`, `bodycaptcha.py:20` | import `hud_font`, `top_bar_height` | neither game uses them (they read `g.top_reserve`); `hud_font` is grid-internal |
| `body_blobs.py:127-129` | `BodyBlobs.active` property | zero callers (grep `\.active\b`) |
| `body_grid.py:40,89-92` + `body_grid_tester.py:24,99` | `activation_rule="max"` | only the tester can select it, from a key (`activation_rule`) that exists in no settings file; games never pass it |
| `body_grid_tester.py:86` | `settings.get("grid", [4,4])` | key `grid` is not in `captcha-settings.json`; tester-only |
| `captcha-settings.json:6` `detection.min_blob_pixels` | read into `DetectionConfig` (`app.py:267`) | `BlobTracker.detect_foreground()` (`IIVision/blob_tracker.py:257-272`) never consults `min_blob_pixels`; only `detect()`/`_extract_blobs` do, which FundingCAPTCHA does not call. **No-op key** in this Element (and a different key of the same name under `shader_app.blobs` *is* live). |
| `shader_app.py` `main()` (`:308-366`) | the shader-only entry | Functionally a subset of `playlist_app.main()` with `videos: []`. Not dead today (docs point at it; `--setup` pin flag only exists here), but one of the two loops should go — see §4. |
| `captcha.service:6-7` comments | "`--mock-camera` to emit fake blobs" | stale wording (no blobs since ADR-0013) |

### CLI flags

- `app.py --test-depth` is documented and live. `body_grid_tester.py --cols/--rows/--debug/--port 8081` are live but undocumented anywhere (`docs/FundingCAPTCHA.md:249-254` shows only a bare invocation that, without `--camera`/`--mock-camera`, goes straight to LIVE with no frames: `body_grid_tester.py:512-513`).
- `playlist_app.py` has no `--setup` pin (only `shader_app.py:311` does) — the one reason `shader_app.main()` still earns its keep.

---

## 3. Duplication

### 3a. Camera thread — `app.py` vs `body_grid_tester.py`

`app.py:218-281` `_camera_thread`/`_camera_inner` and `body_grid_tester.py:190-253` are the same algorithm (Calibrator → `BlobTracker.detect_foreground` → `apply_cam_transform` → `cam_q.put({"type": "foreground", …})`). Differences: tester lacks the `collect` standback gate (`app.py:240-251`), has a different `max_depth_mm` default (4000 vs 2500 — `tester:206` vs `app:269`), and additionally ships raw/delta arrays and calibration debug images (`tester:232-238, 246-253`). `shader_app.start_camera()` (`:186-212`) reuses `app._camera_thread` correctly — the tester should too.

### 3b. Monitoring server — `app.py` vs `body_grid_tester.py`

`app.py:104-213` and `body_grid_tester.py:105-185`: `_ws_clients`, `_mon_loop`, `_app_status`, `broadcast()`, `_send_ws()`, `_ws_handler()`, `_process_request()`, `_run_monitoring()` — ~80 LOC near-verbatim. Only the endpoint names differ (`/api/restart` vs `/api/debug/toggle`).

### 3c. Settings loader — 2 copies

`app.py:80-87` and `body_grid_tester.py:75-82` are byte-identical `load_settings()`. (`shader_app.py:37` and `playlist_app.py:33` import `app.load_settings` — but that import drags in the whole 756-LOC `app.py` module including pygame/asyncio/websockets imports and `sys.path` mutation at `app.py:42-44`, just for a 7-line function and `DIR`.)

### 3d. Camera factory — 3 copies

`app.py:486-494`, `body_grid_tester.py:489-497`, `shader_app.py:197-202`: `MockCamera(width=cam_cfg.get("width",640), height=cam_cfg.get("height",400), fps=cam_cfg.get("fps",10))` vs `OrbbecCamera(serial=…)`. Also note the hard-coded default `height=400` in all three while `captcha-settings.json:70` says 480.

### 3e. Depth-slab / ROI defaults — 7 copies

`{"near_mm": 800, "far_mm": 2500, "slab_id": 0}` and `{"x":0,"y":0,"w":640,"h":400}` appear at `app.py:436-440`, `shader_app.py:240-243`, `body_grid_tester.py:90-91`, `games/bodycaptcha.py:177-178,200-201`, `games/body_keepaway.py:150-152,205-206`. Slab colour fallback `[0, 220, 100]` appears at `app.py:442`, `bodycaptcha.py:410`, `body_keepaway.py:410`, `body_grid_tester.py:297,315,463`. These defaults also disagree with the committed settings (1000–4000 mm, 480×480 ROI), so the fallbacks are silently wrong if a key is dropped.

### 3f. Slab-mask computation — 4 copies

`(fg >= near) & (fg < far)` OR-folded over slabs: `silhouette.py:30-31`, `shadertoy.pack_body:169-170`, `body_grid.py:84` (per cell, with extra `cell > 0`), `body_grid_tester._draw_silhouette:313-317`. One `slab_mask(fg, slabs) -> bool array` would serve all four.

### 3g. `_make_activator` — 2 copies

`games/bodycaptcha.py:175-184` and `games/body_keepaway.py:148-157`: same function, keepaway adds a `defaults["grid"]` fallback.

### 3h. Blow-up: `_Particle`, `_spawn_confetti`, `_draw_confetti`, `_begin_blowup` — 2 copies

`games/bodycaptcha.py:64-78, 356-381, 467-473` vs `games/body_keepaway.py:48-61, 360-385, 488-494`. ~60 LOC each. Moot if keepaway is deleted; otherwise `games/blowup.py`.

### 3i. Levels-path override — 2 copies

`games/bodycaptcha.py:30-46` and `bodycaptcha_editor.py:20-32`: `_LEVELS_DEFAULT`, `_levels_path`, `set_levels_path`, `get_levels_path`. And `_img_load` (pygame → Pillow fallback): `games/bodycaptcha.py:142-156` vs `bodycaptcha_editor.py:39-47` (game version adds an LFS-pointer check the editor lacks). And `DEFAULT_LEVEL`: `bodycaptcha.py:109-110`, `bodycaptcha_editor.py:80-87`, `distribution/package.py:100-107` — three different defaults.

### 3j. Rotation logic — `shader_app.Rotation` vs `playlist_app.Playlist`

`shader_app.py:86-144` and `playlist_app.py:225-334`: `next()` single-item short-circuit, `for _ in range(max(1,len))` draw loop, `reload()`, `failed()` drop-from-bag, `_load_setup()` try/except → identical structure. `Playlist` is a strict superset. Tests duplicate too: `test_shadertoy.py:307-345` vs `test_playlist_app.py:128-203` (`test_render_failure_drops_setup`, `test_single_setup_is_not_*_on_expiry` exist in both).

### 3k. Main loops — `shader_app.main` vs `playlist_app.main`

`shader_app.py:330-362` and `playlist_app.py:365-411`: event handling (`N`/`→`/`R`/Esc + `stage.handle_key`), fps logging every 10 s, teardown — same.

### 3l. Test rig — 5 copies

| Piece | Copies |
|---|---|
| `ctx()` module fixture (EGL → fallback → CI fail/skip), 15 LOC | `test_shadertoy.py:157-171`, `test_endless_sunset.py:22-36`, `test_hunter_bird.py:27-41`, `test_watering_can.py:59-73`, `test_rainbow_poop.py:44-58` (`test_playlist_app.py:11` imports it from `test_shadertoy`) |
| `Rig` class (Renderer + BodyBlobs on fake clock; `run/buf/image/release`) | `test_hunter_bird.py:44-84`, `test_watering_can.py:76-112`, `test_rainbow_poop.py:61-114`; functional equivalent `make/run/buf/image` in `test_endless_sunset.py:39-72` |
| `rect()`, `EMPTY`, `flickering()`, `walking()`, `standing()`, `both()` | all four shader tests |
| GLSL-constant extraction | `test_watering_can.glsl_consts` (`:23-50`, a mini GLSL `const` evaluator with `eval`), `test_rainbow_poop.const` (`:27-34`, regex), `test_endless_sunset.make_with` (`:310-325`, regex rewrite of `common.glsl`); `test_hunter_bird.py:304` hardcodes `PRINT_LIFE_S = 4.0` instead |

~350 LOC of boilerplate; one `shader_test_rig.py` (or `conftest.py`) would hold it.

### 3m. Colour constant tables — 4 copies

`BLACK/WHITE/DK_GREY/MID_GREY/LT_GREY/GREEN/YELLOW/CYAN/RED` in `app.py:65-73`, `body_grid_tester.py:61-68`, `games/grid.py:6-16`, `bodycaptcha_editor.py:50-67` (editor's values differ slightly), `arc.py:21` (`_DK_GREY` "matches app.DK_GREY").

---

## 4. Modularization opportunities

### `app.py` (756 LOC) — mixes 6 concerns

Current contents: settings (80-91), monitoring server (104-213), camera thread (218-281), test-input painter (288-339), plugin loading for games + screensavers (347-403), and a 350-line `main()` (408-752) that holds the whole BG_CAL/SCREENSAVER/GAME state machine as local variables and closures.

Proposed split:

| New module | Moves | Public surface |
|---|---|---|
| `settings.py` (~30) | `DIR`, `SETTINGS*`, `load_settings()`, plus the shared defaults from §3e (`DEFAULT_SLAB`, `default_roi(cam_cfg)`, `slab_color(settings)`) and `sys.path` setup | `load_settings() -> dict`, `DIR`, defaults |
| `monitor.py` (~90) | `_LogHandler`, `/health` JSON, `/logs` WS, `/api/restart` → `threading.Event`. Parameterise the command endpoints so the tester's `/api/debug/toggle` is the same class. | `MonitoringServer(port, commands: dict[str, Event]).start()`, `.set_status(dict)`, `.log_handler` |
| `camera_feed.py` (~90) | `_camera_thread`/`_camera_inner`, `make_camera(cam_cfg, mock)`, the `collect` standback gate, the `cam` dict + `_start_camera`/`_do_restart` closures (`app.py:524-553`) | `CameraFeed(settings, mode).start()/restart()/stop()`, `.queue`, `.collect` |
| `test_input.py` (~55) | `TestInputHandler` | unchanged |
| `plugins.py` (~60) | `_load_games`, `_load_screensavers`, `_NoSaver` (`_NoGame` already lives in `arc.py` — put `_NoSaver` beside it or here) | `load_games(settings, levels_path)`, `load_screensavers(settings)` |
| `kiosk.py` (~250) | `AppState`, the three state branches extracted to `_tick_bg_cal / _tick_screensaver / _tick_game`, with the 15 loose locals (`cal_elapsed`, `cal_started`, `cal_done_seen`, `attract_elapsed`, `saver_elapsed`, `sil_cache`…) as fields of a `Kiosk` dataclass. Also fixes the `R`-key vs HTTP-restart reset blocks being two slightly different copies (`app.py:583-591` resets `sil_cache`; `:598-604` does not). | `Kiosk(settings, args).run()` |
| `app.py` (~40) | argparse + wiring | `main()` |

Then `shader_app.py`/`playlist_app.py` import `settings`/`camera_feed` instead of `app` (today `from app import DIR, _camera_thread, load_settings` pulls pygame display code and a private function across module boundaries).

### `body_grid_tester.py` (626 LOC)

Half of it is §3a–3c duplication. After the split above it becomes: `_build_config` (15), 5 draw functions (180), `main` (180). Two choices:
- **Fold into `app.py --tester`**: it is "app.py without games, with debug overlays". The extra camera payload (raw/delta/cal images) could become an opt-in `debug=True` on `CameraFeed`.
- **Keep standalone at ~300 LOC** using `settings`/`monitor`/`camera_feed`. Either way delete `activation_rule`/`grid` tester-only keys or add them to the settings file.

### `bodycaptcha_editor.py` (847 LOC)

One `Editor` class, 700 LOC, mixing data model, widget toolkit, and three screens.

| New module | Moves |
|---|---|
| `editor/levels_io.py` (~60) | `DEFAULT_LEVEL`, `_load`, `_save`, `_sort_key`, levels-path override, `_all_image_paths`, `_img_load`. **Share with `games/bodycaptcha.py`** (§3i) — one `levels.py` at package root: `read_levels`, `write_levels`, `DEFAULT_LEVEL`, `set/get_levels_path`, `load_image`. |
| `editor/widgets.py` (~130) | `_label`, `_text_field`, `_stepper`, `_labeled_stepper`, `_btn_row`, `_btn`, `_wrap`, colour table |
| `editor/level_model.py` (~90) | the mutation methods `_toggle … _del_level`, `_align/_set_align`, `_grid_dims`, `_vset` — pure, testable without pygame |
| `editor/views.py` (~300) | `_draw_grid`, `_draw_picker`, `_sidebar`, `_align_pad`, geometry (`_cell_size`, `_preview_rect`, `_thumb_rects`) |
| `bodycaptcha_editor.py` (~80) | `Editor.run()` event loop + argparse |

Also: `Editor.__init__` calls `pygame.display.set_mode` — tests (`test_bodycaptcha_editor.py:22-33`) have to open a dummy display to test crop maths; the model split fixes that.

### `shadertoy.py` (468 LOC)

Already has clear sections. Split along the line its own docstring draws ("Pure helpers … need no GL; Renderer needs a moderngl context"):
- `shadertoy/setup.py` (~90): `Setup`, `load_setup`, `wrap_source`, `_HEADER/_FOOTER`, `SOURCES`, `ShaderError`
- `shadertoy/body.py` (~70): `pack_body`, `BodyMouse`
- `shadertoy/keyboard.py` (~40): `js_keycode`, `Keyboard`
- `shadertoy/blobs_contract.py` (~10): `BLOB_SLOTS/ROWS/states` (so `body_blobs.py` stops importing the renderer module for 6 constants)
- `shadertoy/renderer.py` (~220): `_PingPong`, `Renderer`, `_idate`
Low urgency; the file is coherent. Do it only if `body_blobs → shadertoy` import direction bothers you.

### `shader_app.py` + `playlist_app.py` (791 LOC together)

`Playlist ⊇ Rotation`, `playlist_app.main ⊇ shader_app.main`. Proposal:
- Delete `Rotation` and `shader_app.main()`; give `playlist_app` a `--setup NAME` flag that builds a one-item playlist. `shaders/setups.json` and `playlist.json:setups` are also two lists of the same thing — keep `playlist.json` (it already carries `setup_duration_s`), delete `setups.json`, point `test_shadertoy.py:179` at the playlist.
- Rename what remains of `shader_app.py` → `shader_stage.py` (`ShaderStage`, `open_display`, `start_camera`, `drain_camera`, `add_mode_args`, `_TestMouse`) — a library, not an app.
- `playlist_app.py` then splits: `video_player.py` (`VideoPlayer`, `VideoScreen`, `fit_rect`, GLSL strings — 150 LOC) and `playlist_app.py` (`Item`, `Playlist`, `main` — 200 LOC).
- `docs/FundingCAPTCHA.md:74` and `deploy/captcha.service` comment then point at one shader entry point.

### `games/body_keepaway.py` (498) / `games/bodycaptcha.py` (477)

If keepaway is deleted, bodycaptcha is the only game and the remaining split is: `games/levels.py` (shared with editor, §above), `games/blowup.py` (`_Particle`, confetti spawn/draw — 60 LOC, reusable by any future Game), leaving `bodycaptcha.py` ~350. If keepaway stays, also extract `games/activator.py` (`_make_activator`) and let both import `blowup`.

### `games/grid.py` (258)

After deleting the dead members (§2) it is ~200 LOC and splits naturally: `grid.py` (`Grid`, ~60) and `shell.py` (ADR-0019 renderers + caches + `hud_font`, ~130). ADR-0019 itself suggested `games/shell.py`.

### The shader behaviour tests (`test_watering_can.py` 1097, `test_hunter_bird.py` 667, `test_endless_sunset.py` 601, `test_rainbow_poop.py` 439 = 2,804 LOC)

**Are they reimplementing shaders in Python?** Partly, and that part is the fragile part.

What they *do* (good): run the real GLSL on a real (llvmpipe) GL context with the real `BodyBlobs` tracker on synthetic masks, then read buffers back and assert behaviour ("walking rewinds growth", "standing never strikes", "splat lands on the head"). That is black-box behaviour testing of team-authored content and it has caught real bugs (the `--test-input` keyboard texture fix noted in ADR-0022).

What is unsustainable:
1. **Buffer-layout knowledge is duplicated into the tests.** `test_watering_can.Rig.person/base/ghost/sun` (`:102-105`), `test_hunter_bird.Rig.slot/head/attn/reticle/mood/blink/stamp/prints` (`:70-77`), `test_rainbow_poop.Rig.slot/anchor/poop/drop/splats/grounds` (`:99-104`) each mirror the texel map at the top of the Setup's `common.glsl`. Any layout change breaks dozens of tests. These are implementation-detail tests of storage, not of what the visitor sees.
2. **Shader maths re-derived in Python.** `test_watering_can.py:318-329` `grown()/seconds_to()` reimplement the GLSL growth curve from `GROW_EARLY`, `GROW_EARLY_S`, `GROW_S`; `test_rainbow_poop.py:40-41` `FALL_S = (SPAWN_Y - HEAD)/FALL_SPEED`; `test_hunter_bird.py:100` `walking()` docstring computes "motion ≈ 0.57 so lock stays < 1 for 6 s at the defaults". When a tunable is retuned, the tests follow only if the Python formula still matches the GLSL formula — that's the reimplementation trap. `test_watering_can.glsl_consts` goes furthest: a 25-line GLSL `const` expression evaluator using `eval`.
3. **Three different mechanisms** for reading GLSL constants (§3l). Pick one and ship it as a helper.
4. **Magic tolerances everywhere** (`< 0.06`, `< 0.15 * …`, `>= merged - 0.05`, `abs(fall - 1/LEAVE_S) < 0.15/LEAVE_S`) tuned to llvmpipe half-float behaviour. `test_watering_can.py:271-292` even parametrises on slot 7 "the coarsest half-float spacing". These will flake on a different Mesa version.
5. **Scale**: 1,097 LOC to test a 1,069-LOC shader is a 1:1 ratio; each test runs tens to hundreds of GL frames; `test_hunter_bird.BigRig` renders a 480×480 Body ×40 frames ×3. CI time will balloon with each new Setup.

**Recommendation:**
- Keep the GL behaviour tests, but shrink each to the **spec-level claims** in its design doc (`docs/superpowers/specs/*.md`, ~100 lines each): ~10-15 tests per Setup, not 40-75. Delete the layout-probing tests (`test_owner_is_record_slot`, `test_run_extents_span_leg_to_shoulder`, `test_slot_tracks_record_id`, `test_records_layout…`) or move them to one `test_shader_contracts.py` that checks only the *inputs* contract (Buffer A, blobs texture) which is what `shadertoy.py`/`body_blobs.py` own.
- Extract `shader_test_rig.py`: `ctx` fixture, `Rig`, mask builders (`rect/person/walking/flickering/both`), `glsl_consts()`, `read_buffer()`. Target ~200 LOC shared, removing ~350 LOC of copies.
- Move the five test files into `shaders/<name>/test_<name>.py` next to the GLSL they test (pytest will still collect them via `testpaths = ShowControl`), so a Setup is a self-contained folder and a deleted Setup takes its tests with it.
- Stop re-deriving curves in Python: where a test needs "growth after 10 s", read it from the shader (render 10 s, record the value once as an approved fixture) rather than from a Python copy of the formula — or assert monotonicity/ordering, not values.
- Add a frame-count budget: a single `pytest -m gl --durations` check in CI so the suite can't double silently.

---

## 5. Config sprawl

### Files

`captcha-settings.json` (+ optional `captcha-settings.local.json`, shallow-merged — **gitignored**, contrary to docs), `bodycaptcha-levels.json`, `taunts.json`, `keepaway-body-levels.json`, `keepaway-body-taunts.json`, `screensavers.json`, `playlist.json`, `shaders/setups.json`, `shaders/*/setup.json`, `deploy/private-assets.example.env`, `ShowControl/network.json` (via OSCFabric).

### `captcha-settings.json` key → readers

| Key | Readers | Notes |
|---|---|---|
| `detection.depth_delta_mm` | `app.py:266`, `tester:203` | live (`BlobTracker.threshold_map`) |
| `detection.min_blob_pixels` | `app.py:267`, `tester:205` | **no-op**: `detect_foreground` ignores it (`IIVision/blob_tracker.py:257-272`) |
| `detection.min_depth_mm` | `app.py:268`, `tester:205` | live (`Calibrator` valid mask, `blob_tracker.py:190`) |
| `detection.max_depth_mm` | `app.py:269`, `tester:206` | **likely no-op** for foreground path (`blob_tracker.py:186` "No upper cap"; `:300` is in `detect()`); defaults disagree 2500 vs 4000 |
| `depth_slabs[]` | `app.py:436`, `shader_app.py:240`, `tester:91`, `bodycaptcha.py:178,200`, `body_keepaway.py:151,205` | live |
| `slab_styles` | `app.py:441`, `tester:463`, `bodycaptcha.py:409`, `body_keepaway.py:409` | live, but every reader hardcodes `["0"]` except the tester; multi-slab styling is tester-only |
| `cell_activation_threshold` | `tester:98`, `bodycaptcha.py:180`, `body_keepaway.py:153` | live |
| `camera_roi` | `app.py:438`, `shader_app.py:241`, `tester:90`, games | live |
| `silhouette_dilation_px` | `app.py:236`, `tester:211` | live |
| `attract_dwell_s`, `min_foreground_pixels`, `silhouette_opacity` | `app.py:443-445`; `min_foreground_pixels` also `shader_app.py:256` | live |
| `calibration_frames` | `app.py:232,564`, `tester:209,525` | live |
| `calibration_countdown_s` | `app.py:450` | live, app only |
| `calibration_standback_s` | `app.py:451`, `shader_app.py:206` | live |
| `bodycaptcha.{timer_s,hold_s,hold_decay_rate,hint_opacity,intensity_weights}` | `bodycaptcha.py:197-199,242-266` | live |
| `keepaway_body.*` | `body_keepaway.py` only | **dead** |
| `shader_app.render_scale`, `.fps` | `shader_app.py:237,318`, `playlist_app.py:350` | live |
| `shader_app.blobs.*` (7 keys) | `shader_app.py:255` → `BlobConfig.from_dict` | live; `from_dict` silently drops unknown keys (`body_blobs.py:49-51`) so a typo is invisible |
| `camera.serial/width/height/fps` | `app.py:488-494`, `shader_app.py:197-202`, `tester:491-497` | live; code default height 400 ≠ file 480 |
| `camera.pos_cm`, `camera.rotation` | `silhouette.py:47-48` | live |
| `_comment`, `_silhouette_dilation_px` | — | documentation keys (fine, but the convention is inconsistent: one has `_` prefix per key, others a block `_comment`) |

### Keys read but absent from any file

- `grid` (`tester:86`), `activation_rule` (`tester:99`) — tester-only.
- `keepaway_body.grid` default `[8,6]` — dead.

### Two JSON lists of Setups

`shaders/setups.json` (shader_app) and `playlist.json:setups` (playlist_app) must be kept in sync by hand; today they match. See §4.

### Defaults scattered in code

Every `settings.get(key, default)` site carries its own default; §3e counted 7 copies of slab/ROI defaults with values that disagree with the committed file. A single `settings.py` with a `DEFAULTS` dict (or a dataclass) is the fix; then `captcha-settings.json` can be validated against it at startup and typos (`shader_app.blobs.*`) surface as warnings.

---

## 6. Docs drift

### `docs/FundingCAPTCHA.md`

| Line | Claim | Reality |
|---|---|---|
| 11, 162-170 | "lightweight HTTP/WebSocket monitoring server"; "`http://<host>:8080/` — small HTML page with state + live log stream… Current Game + Level, Live intensity value, Last 100 log lines" | `GET /` returns a JSON blob (`app.py:189-194`). No HTML, no game/level/intensity in `_app_status` (the only fields ever broadcast are `state`, `progress`, `phase`, `remaining_s`, `fg_pixels`, `error`), no log history buffer (`_LogHandler` streams live only). The HTML lives in `ShowControl/Dashboard/fundingcaptcha.html`. |
| 93 | `captcha-settings.local.json` "not gitignored, but per-host" | It **is** gitignored (`.gitignore:19`, under a stale comment about `touch_test_pygame.py`). And `app.py:551` wipes it on restart. |
| 108 | "Per-game blocks: `bodycaptcha`, `keepaway_body` (timer_s, hold_s, hold_decay_rate, grace_s, abandon_s, weights…)" | keepaway never loads; `hint_opacity` omitted from the list |
| 137 | Keepaway "Module and its Level/taunt data retained for a future return" | accurate, but the retention is the problem (§2) |
| 146 | `pipes_3d.py` "(Windows-style 3D pipes screensaver)" | it is a garden-vines reskin (`pipes_3d.py:1-5`) |
| 152 | "sends to the TreeHouse Hub **each frame**" | intensity is throttled to 10 Hz (`app.py:741`) |
| 158 | `/captcha/mode` `s` (in) "from Dashboard" | `app.py` has no OSC receiver; `FabricClient` is outbound only. Nothing in the directory listens on `network.json` `captcha.osc_port 9003`. |
| 249-254 | `python3 body_grid_tester.py` | without `--camera`/`--mock-camera` it enters LIVE with no frames (`tester:512-513`); flags `--cols/--rows/--debug/--port 8081` undocumented; keys `D`/`C` undocumented |
| 128 | `distribution/` Windows editor build | probably abandoned (§2) |
| 74 | shader player "Not yet verified on the Pi 5 under kmsdrm" | written 2026-10-30; four Setups and a playlist player later, nobody has updated this. Either verify or keep — but a doc that says "unknown" for weeks is noise. |
| 40-48 | `app.py` flags table | omits `--levels` (documented only at :306) |

### `docs/games/bodygrid.md`

- "`BodyGridActivator` class (in `games/grid.py`)" — it is in `body_grid.py`.
- "Returns a set of `(col, row)` pairs" — returns `dict[(col,row) → [(slab_id, coverage)]]` (`body_grid.py:43`).
- "Standalone tester … logs active cells each frame" — it broadcasts a count over a WebSocket nobody connects to (`tester:590`).
- "Grid dimensions and `cell_activation_threshold` are configurable per-Level" — threshold is global only (`bodycaptcha.py:180`).

### `docs/games/bodycaptcha.md`

- "Status: In implementation (2026-05-13)" — shipped.
- "Hold timer **resets** if any extra cell is covered" — it drains at `hold_decay_rate` since #150 (`bodycaptcha.py:349-350`).
- Visual table: "Hold active → Green + hold progress bar shown" — ADR-0019 replaced the bar with a perimeter ring (`grid.py:193-203`).
- Config block omits `hold_decay_rate`; default `hint_opacity` shown as 0.1, file says 0.2 (`captcha-settings.json:40`).
- Level format omits `crop_align`.

### `docs/games/keepaway.md`

- "Status: Implemented as … body_keepaway.py" — implemented but **not loaded** (`app.py:349`).
- API block shows `update(self, activations, foreground, dt)` — actual is `update(foreground, dt)` (`body_keepaway.py:267`).
- "Timer: Countdown bar across the top … green → yellow → red" — now the ADR-0019 numeric timer (`body_keepaway.py:463`).

### `docs/games/rhythm.md`, `upsidedown.md`

Design notes for code deleted in ADR-0013 (2026-05), "Port TODO" ever since. Either track them as issues or delete; as docs they describe nothing in the tree.

### `CONTEXT.md:76`

"Examples: BodyCaptcha, UpsideDown, Rhythm, Keepaway. `app.py` loads all Games and plays them in shuffle-bag order." — one Game exists and is loaded; three of the four names are deleted or dead.

### `AGENTS.md` / `docs/agents/running-and-testing.md:6`

"`make test` runs Node tests (FundingCAPTCHA)" — the only Node test ever, `touch-input.test.js`, was deleted with the browser stack on 2026-05-10 (`4caa60b`). The only `.js` left in the repo is `FlowerBeds/layout_tool/layout.js` and there is no `package.json`, so `node --test` tests nothing.

### Git-history context (full history, 207 commits from 2026-01-24)

`ShowControl/FundingCAPTCHA` was rebuilt in the May 2026 pre-show crunch: browser stack deleted 2026-05-10, touch calibrator added and removed the same month, `screen_projector.py`/`pairs.json`/`rhythm-images.json`/`keepaway-images.json` deleted 2026-05-24, Keepaway ported 2026-05-22 (#90) then unplugged 2026-09-06 (#142). Since June the only churn in the kiosk path has been #142–#152 (Sept); everything since 2026-10-30 is the shader player. `games/grid.py`, `body_grid.py`, `ScreenSavers/*`, `keepaway-body-*.json` and all images have not changed since May.

### ADRs

**ADR-0012** (unified pygame app): describes `AppStateMachine BG_CAL → CORNER_CAL → LIVE`, Games "UpsideDown, Rhythm, Keepaway", `pairs.json`/`rhythm-images.json`/`keepaway-images.json`, "WS /ws → pushes blobs, touch state", "Dashboard … touch debug visualisation". All superseded by ADR-0013 but ADR-0012 carries no "Superseded/Amended by" header (ADR-0013 does say it supersedes 0004/0011, not 0012). `POST /api/restart` is actually method-agnostic (`app.py:181` matches path only).

**ADR-0013** (silhouette interaction):
- "Hold timer … Covering any extra cell resets the hold timer" — drain since #150.
- "Blob detection is not used by FundingCAPTCHA" — true for `app.py`; false since ADR-0022 (`body_blobs.py:30` runs `BlobStabilizer`). ADR-0022 amends 0021, not 0013.
- "`camera_roi` (crop, display-space coordinates)" vs `docs/FundingCAPTCHA.md:102` "in camera pixel coords" — contradictory; code crops the post-transform frame (`body_grid.py:62`), i.e. display-space-at-camera-resolution.
- "BodyGrid is the first Game built" — the Game is BodyCaptcha; Body Grid is the input layer (CONTEXT.md:85 warns about exactly this conflation).
- Level format omits `hold_decay_rate`, `crop_align`.
- Consequences list "UpsideDown, Rhythm, and Keepaway must be ported… Code deleted pending port" — six months on, only Keepaway was ported and then unplugged.

**ADR-0016** (test input): accurate except "Brush radius … ~20px" (code: 15, `app.py:296`). Good ADR.

**ADR-0019** (UI shell): "`draw_hud_label`, `draw_progress_bar` become unused and should be deleted" — done. But it left `Grid.flash/draw_flashes/blit_cell/inner_rect/draw_background/CELL_PAD` and the 7 colour aliases behind (§2). Its "Implementation choice (helpers in grid.py vs games/shell.py) is left to the implementer" — implementer chose grid.py; §4 suggests finishing the move.

**ADR-0021** (shader player): accurate. "Not yet measured on the Pi 5: frame rate per Setup" — still unmeasured per docs. Doesn't mention `playlist_app.py` / `setup_duration_s` override (only `docs/FundingCAPTCHA.md:78-87` does) — fine as the ADR predates it, but a one-line amendment note would help.

**ADR-0022** (blob records): accurate against `body_blobs.py` and `shadertoy.py`. "Tracking runs only while the current Setup binds blobs, and resets when a Setup that doesn't is playing" — code resets on every load via `on_load=stage.blobs.reset` (`shader_app.py:325`), which is stronger than stated; fine.

### Deploy

- `deploy/captcha.service:1` `Description=FundingCAPTCHA Game Server` and `:7` "Use `--mock-camera` to emit fake blobs" — `server.py` era wording.
- `.gitignore:18-19` comment "written by touch_test_pygame.py" — that file no longer exists.

---

## 7. Test coverage gaps and test quality

### No tests at all

| Module | LOC | Risk |
|---|---|---|
| `app.py` main loop / state machine | ~350 | The show path. BG_CAL→SCREENSAVER→GAME transitions, standback/countdown gating (`:649-687`), attract dwell, OSC throttling, R/HTTP restart — zero coverage. Only `_load_games` is tested (`test_app_games.py`). The `_save_local({})` bug would have been caught by any restart test. |
| `app.py` monitoring server | ~110 | untested; `/ws` has no client either |
| `app.py` `TestInputHandler` | 55 | untested |
| `app.py` `_camera_thread` | 65 | untested (needs a fake camera; `MockCamera` exists) |
| `body_grid_tester.py` | 626 | untested |
| `games/body_keepaway.py` | 498 | untested (and dead) |
| `games/grid.py` | 258 | untested — `Grid` letterbox maths, `_fit_prompt_font`, `_wrap_to_width`, `draw_center_text` binary search; pure-ish and cheap to test |
| `games/bodycaptcha.py` `_LevelBag` | 25 | untested — the difficulty-progression rule ("same or +1", fallback to all) is a spec claim in ADR-0013 with no test |
| `games/bodycaptcha.py` blow-up / WIN_FLASH / DONE transitions | ~80 | `test_bodycaptcha_hold.py` covers PLAYING→WIN_FLASH only; timer expiry → BLOWUP → DONE → `"loss"` is untested |
| `shader_app.ShaderStage`, `_TestMouse`, `start_camera`, `drain_camera`, `open_display` | ~200 | untested except `Rotation` |
| `playlist_app.VideoScreen`, `main` | ~100 | untested |
| `ScreenSavers/waiting.py` | 42 | untested (and a stub) |
| `distribution/*.py` | 297 | untested |
| `silhouette.build_cam_transform` | 17 | untested |
| `shadertoy.Renderer.release` / `_PingPong` lifecycle | | untested (GL resource leaks on Setup reload would only show on the Pi) |

### Tests that test implementation details / are brittle

- **All four shader behaviour tests** read private renderer state: `rig.r._buffers[name].read_tex` (`test_watering_can.py:99`, `test_hunter_bird.py:67`, `test_endless_sunset.py:66`, `test_rainbow_poop.py:96`) — a private attribute of `Renderer`. Add `Renderer.read_buffer(name)` as public API (it already has `read_body()`).
- Texel-layout probing (§4): `test_watering_can.py:236-240 test_owner_is_record_slot`, `:218-224 test_run_extents_span_leg_to_shoulder`, `:243-253 test_walker_leaves_no_hold_trail` (asserts `floor(0.9/HOLD_Q)*HOLD_Q/0.9` encoding), `test_hunter_bird.py:125-129 test_slot_tracks_record_id`, `test_rainbow_poop.py:307-314 test_ages_keep_time_in_half_floats`. These pin storage decisions.
- Half-float tolerance tuning: `test_watering_can.py:271-273` parametrises slot 7 "coarsest half-float spacing"; `:598` "a half float stalls the easing short of full"; `:610` "a half float stalls small steps". These encode llvmpipe f16 behaviour; a Mesa upgrade can flip them.
- `test_watering_can.glsl_consts` (`:23-40`) uses `eval()` on GLSL source — a mini-interpreter inside a test file.
- `test_endless_sunset.make_with` (`:310-325`) rewrites `common.glsl` with regex and recompiles — tests depend on the exact `const float NAME =` formatting of the shader.
- `test_hunter_bird.py:304` `PRINT_LIFE_S = 4.0` hardcoded while the other three Setups read constants from GLSL.
- `test_bodycaptcha_editor.py:22-33 editor fixture` constructs the full `Editor` (opens a display) to test `_align()` string logic — the model/view split (§4) fixes this.
- `test_app_games.py:19-20` opens a pygame display at module import; `test_bodycaptcha_hold.py` and `test_bodycaptcha_levels.py` do the same because `BodyCaptchaGame.__init__` reads `pygame.display.get_surface()` (`bodycaptcha.py:202`). Pass `(WW, WH)` into the constructor instead.
- `test_bodycaptcha_levels.py:68,139` imports mid-file (`# noqa: E402`) — three test modules glued into one.
- `test_playlist_app.py:11` `from test_shadertoy import SOLID, ctx` — cross-test-module import; belongs in a `conftest.py`.
- Global-state leakage: `set_levels_path` is module-global in `games/bodycaptcha.py:30-36`; two test files need `autouse` fixtures to restore it (`test_bodycaptcha_levels.py:71-75`, `test_bodycaptcha_editor.py:138-141`), and `test_app_games.py:45-50` exists only to assert "override leaked from a previous test" didn't happen. A `Levels` object passed to the game would remove all three.
- `ScreenSavers/test_pipes_3d.py:16-21` reimplements `importlib` module loading that `app._load_screensavers` also does — a third copy of the loader.

### CI

`.github/workflows/tests.yml:25-26` installs Mesa so GL tests run; the `ctx` fixtures `pytest.fail` under `CI=1` if no context — good. `requirements-dev.txt` lacks `av` (so `test_playlist_app` video tests `importorskip` → silently skipped in CI; `:49,94`), `Pillow`, and `websockets` (fine today since both are lazily imported). The GL suite is already 2,800 LOC / several hundred rendered frames per test file; no duration budget.

---

## 8. Deletable LOC estimate

| Item | LOC | Confidence |
|---|---|---|
| `games/body_keepaway.py` + its JSON + settings block | ~545 | high (never loaded, asserted by test) |
| `body_grid_tester.py` duplicated infra (monitoring/camera/settings/colours) | ~170 | high (if shared modules exist) — or 626 if folded into `app.py --tester` |
| `distribution/` (3 scripts + READMEs + `sys.frozen` branch) | ~300 py (+150 docs) | medium — confirm no active Windows teammate |
| `ScreenSavers/waiting.py` | 42 | high |
| `games/grid.py` dead members + aliases | ~45 | high |
| `app.py`: `_save_local`, unused colours, empty section, `/ws` channel + `broadcast` | ~60 | high (`/ws`: medium — confirm no client) |
| `shader_app.Rotation` + `shader_app.main` + `setups.json` (after `playlist_app --setup`) | ~120 | medium |
| Duplicate camera factories / slab defaults / colour tables after `settings.py` | ~60 | high |
| Test rig boilerplate (5× `ctx`, 4× `Rig`, 4× mask helpers, 3× const readers) | ~350 | high |
| Layout-probing / half-float shader tests | ~200-400 | medium (judgement call per test) |
| `body_blobs.active`, keepaway-only imports, misc | ~15 | high |
| **Total** | **~1,500 conservative / ~2,100 aggressive** | of 10,992 Python LOC (14–19%) |

Plus 16 LFS images and ~300 lines of stale docs (`docs/games/rhythm.md`, `upsidedown.md`, half of `keepaway.md`, ADR-0012's body).

---

## 9. Ranked refactors (value ÷ effort)

1. **Delete dead code + fix `_save_local` bug** (keepaway, waiting.py, grid.py members, app.py leftovers, unreferenced images, `detection.min_blob_pixels` key). ~700 LOC gone, one show-affecting bug fixed, zero design decisions. Half a day.
2. **Extract `settings.py` + `camera_feed.py` + `monitor.py` from `app.py`; make `body_grid_tester.py` and `shader_app.py` import them.** Removes §3a–3e (≈230 LOC), fixes the `from app import _camera_thread` cross-module private import, makes the defaults agree with the file. One day.
3. **Collapse `shader_app`/`playlist_app`**: `playlist_app --setup`, delete `Rotation` + `shader_app.main` + `setups.json`, rename the remainder `shader_stage.py`, split out `video_player.py`. One show entry point for shaders instead of two, one Setup list instead of two. Half a day + doc update.
4. **`shader_test_rig.py` (or `conftest.py`) + public `Renderer.read_buffer()`**; move each Setup's tests into its own folder; prune layout-probing tests to spec-level behaviour. −350 LOC boilerplate immediately, and the only way the Setup test suite stays maintainable as Setups are added. One to two days.
5. **Split `app.main()` into a `Kiosk` class with per-state tick methods, and `bodycaptcha_editor.py` into model/widgets/views; share `levels.py` between game and editor.** Biggest readability win for small-context readers (756- and 847-LOC files → ≤300 each), enables the first real tests of the show state machine. Two to three days; do after 1–2 so the file is already smaller.

Docs: after #1–3, rewrite `docs/FundingCAPTCHA.md` §Monitoring, §Settings (`.local` is gitignored; drop `keepaway_body`; drop `/captcha/mode`), §Games, §Body Grid tester; mark ADR-0012 "Superseded by ADR-0013"; add "Amended by ADR-0022" to ADR-0013's blob-detection paragraph; delete `docs/games/rhythm.md`/`upsidedown.md` (or convert to issues); fix `CONTEXT.md:76`; fix `AGENTS.md` "Node tests (FundingCAPTCHA)".
