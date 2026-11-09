# Audit — ShowControl core (IIVision, FlowerBeds, TreeHouse, Dashboard, OSCFabric, scripts, CI)

Read-only audit, 2026-11-09. Scope excludes FundingCAPTCHA and PlayingThePipes except where they
import in-scope code. All paths relative to `the repo root`. Git facts come from the
full 207-commit history (2026-01-24 → 2026-11-08); the May 2026 spike (108 commits) was the
pre-show crunch, after which in-scope Python has barely moved (TreeHouse: 3 commits since June;
FlowerBeds/Dashboard/OSCFabric/IIVision-core: zero functional commits since 2026-05-29).

Test baseline: `python3 -m pytest IIVision ShowControl/FlowerBeds ShowControl/TreeHouse
ShowControl/OSCFabric scripts` → **116 passed** (2.5 s). `node --test` at repo root → **0 tests**.

---

## 0. Headline findings (blunt)

1. **The TreeHouse Python LED pipeline has no consumer in the current show.** ESP32-S3 controllers
   (ADR-0020/0021) ignore Garden State and animate standalone; three *additional* standalone Pico
   firmwares exist (`Firmware/Club_Pico`, `HouseSwarming_Pico`, `Fungi_Pico`, all docstring'd
   "stopgap", 2026-05-29). Meanwhile `coordinator.load_config` reads `raw.get("pico")`
   (`coordinator.py:177`) but `settings.json` only has `pico_dioramas`/`pico_structure`
   (`settings.json:2-10`), so the one `PicoDriver` opens `/dev/ttyACM0` by default — and
   `dormer.pico_pin: 0`, `porch_lights.pico_pin: 1` collide with `dioramas[0..1].pico_pin` on
   that single serial link. ≈650 LOC (`displays/led.py`, `effect.py`, `porch_lights.py`,
   `pico_driver.py`, `LEDControllable`/`ChannelFrame`, half of `coordinator.py`,
   `test_forge_and_flora.py`, Dashboard LED-pattern UI) is live-but-inert. Needs an explicit
   keep/kill decision; ADR-0020 already promised removal "once hardware is installed".
2. **Two Dashboard→TreeHouse controls are broken at the call site.**
   `visualizer.py:112` calls `_coordinator.set_forge_mode(...)` — no such method exists on
   `Coordinator` (AttributeError → 500). `Dashboard/treehouse.html:45-47` sends show modes
   `full`/`dim`/`off`; `ShowMode` is `active`/`dim`/`inactive` (`displays/base.py:10-13`,
   renamed by ADR-0007), so two of three buttons log "Unknown show mode".
3. **FlowerBeds has no OSC listener at all** (no `Dispatcher`/`osc_server` in
   `ShowControl/FlowerBeds/*.py`). `docs/FlowerBeds.md:103` documents `/flowerbeds/mode` as
   inbound; ADR-0007 requires it; `Dashboard/serve.py:78` relays it into the void.
4. **IIVision ships ~140 LOC of dead camera code.** `OrbbecRGBCamera` + `RGBFrame`
   (`camera.py:38-53, 303-425`) existed only for the ArUco layout calibrator deleted by ADR-0015;
   nothing imports them; `cv2` (needed at `camera.py:409-412`) is not in any requirements file.
5. **AGENTS.md constraint #1 names a function that does not exist.** `IIVision.Blob3D.world_pos_cm()`
   — `Blob3D` (`blob_tracker.py:76-83`) has no such method; the conversion is
   `IIVision.transforms.orbbec_to_world()` (`transforms.py:62-73`). Repeated in
   `docs/agents/python-conventions.md:28`.
6. **AGENTS.md constraint #3 / `docs/agents/firmware.md:9` claim FlowerBeds firmware reads a
   generated `config.h`.** It does not: `Firmware/FlowerBeds_Follow_ServoController/*.ino:26`
   hardcodes `IPAddress ip(192,168,1,51)`, and `scripts/hooks/firmware_config_gen.py:20` says
   `TODO: generate ... config.h too`. Also `flower_beds.py:129-131` `ControllerConfig` hardcodes
   `"192.168.1.50"` (and is unused).
7. **`make test` is misdocumented.** AGENTS.md/running-and-testing.md say it "runs Node tests
   (FundingCAPTCHA)"; there are no `*.test.js` files or `package.json` anywhere — `node --test`
   reports `# tests 0`. Only JS in the repo is `FlowerBeds/layout_tool/layout.js`.
8. **No packaging anywhere** (no `pyproject.toml`/`setup.py`/`conftest.py`). Elements reach
   IIVision/OSCFabric via `sys.path.insert` (`FlowerBeds/main.py:32,53`) and tests only work via
   `python -m pytest` from repo root (cwd on `sys.path`). TreeHouse and Dashboard don't use
   OSCFabric at all — they re-implement `network.json` loading.

---

## 1. Inventory

Legend — **P** production show path, **O** operator tool, **D** dev/test only, **X** prototype /
abandoned / dead. LOC = `wc -l`. "Importers" = files outside the file's own directory that import it
(grep across whole repo).

### IIVision/ (1,582 LOC)

| File | LOC | Purpose | Importers | Class |
|---|---|---|---|---|
| `__init__.py` | 47 | Re-exports public API (incl. dead `OrbbecRGBCamera`, `RGBFrame`) | FlowerBeds/main.py, FundingCAPTCHA app.py/shader_app.py/body_grid_tester.py/silhouette.py | P |
| `blob_tracker.py` | 434 | `Calibration`, `Calibrator`, `BlobTracker`, `FramePacket`, `DetectionConfig`, `Blob2D/3D` | pipeline.py, camera.py, silhouette_warp.py, FundingCAPTCHA (`detect_foreground`, `threshold_map`, `CameraIntrinsics`) | P |
| `blob_stabilizer.py` | 196 | `BlobStabilizer`, `StabilizerConfig`, `TrackedBlob`, `TrackState` | pipeline.py, FlowerBeds flower_beds.py/test, FundingCAPTCHA body_blobs.py | P |
| `camera.py` | 425 | `OrbbecCamera`, `MockCamera`, **dead** `OrbbecRGBCamera`/`RGBFrame` | FlowerBeds main.py, FundingCAPTCHA ×3 | P (lines 303-425: X) |
| `transforms.py` | 92 | `Rotator`, `Transform`, `rotator_to_matrix`, `transform_position`, `orbbec_to_world`, `look_yaw_degrees` | pipeline.py, silhouette_warp.py, FlowerBeds flower_beds.py/main.py | P |
| `pipeline.py` | 108 | `build_calibration`, `run_pipeline`, `filter_positions_near_points` | FlowerBeds main.py, flower_beds.py | P |
| `silhouette_warp.py` | 80 | `reproject_silhouette` (FundingCAPTCHA only) | FundingCAPTCHA silhouette.py | P (not in architecture.md table) |
| `test_blob_stabilizer.py` | 45 | `update_tracks()` tests | — | D |
| `test_detect_foreground.py` | 155 | `detect_foreground()` tests | — | D |

No tests cover `Calibrator.build`, `BlobTracker.detect`, `_compute_3d_blobs`, `transforms.py`,
or `pipeline.run_pipeline`.

### ShowControl/FlowerBeds/ (3,652 LOC incl. 848 settings.json)

| File | LOC | Purpose | Importers | Class |
|---|---|---|---|---|
| `main.py` | 454 | CLI, config load, calibration persistence, frame loop, two motor-calibration modes | — (entry) | P |
| `flower_beds.py` | 379 | Config dataclasses, `Attraction`, `FlowerCluster`, `FlowerModule`, `Coordinator`, `MotorCommand` | main.py, test_flower_beds.py | P |
| `visualizer.py` | 434 | FastAPI WS server + 240-line embedded HTML/JS client; `broadcast()`, `/logs` | main.py (lazy), flower_beds.py (TYPE_CHECKING only) | P |
| `diag.py` | 73 | `/cg/ff/ping`→`/cg/ff/pong` client, `parse_found_ids` | main.py, layout_tool.py, test_diag.py | P/O |
| `layout_tool.py` | 246 | FastAPI server for operator layout GUI (port 8764) | test_layout_tool.py | O |
| `layout_tool/index.html` | 48 | GUI shell | layout_tool.py (served) | O |
| `layout_tool/style.css` | 42 | GUI styles | — | O |
| `layout_tool/layout.js` | 569 | Canvas drag/aim/save client | index.html | O |
| `settings.json` | 848 | 12 modules × 4 clusters, cameras, stabilizer, attraction | main.py, layout_tool.py | P |
| `requirements.txt` | 9 | numpy scipy python-osc fastapi uvicorn **aiofiles** websockets pyorbbecsdk2 | — | P (`aiofiles` imported nowhere) |
| `deploy/flowerbeds.service` | 22 | systemd unit | deploy/install.sh | P |
| `deploy/install.sh` | 40 | apt numpy/scipy + pip + unit install | scripts/deploy.sh, install-services.sh | P |
| `test_flower_beds.py` | 140 | yaw clamp / module yaw tests | — | D |
| `test_diag.py` | 88 | ping/pong parse tests | — | D |
| `test_layout_tool.py` | 260 | FastAPI TestClient tests | — | D |

### ShowControl/TreeHouse/ (3,793 LOC incl. 549 club_messages.txt)

| File | LOC | Purpose | Importers | Class |
|---|---|---|---|---|
| `main.py` | 219 | CLI, asyncio supervisor (weston, 2 renderers), frame loop | — (entry) | P |
| `coordinator.py` | 485 | 9 config dataclasses + `load_config` (reads settings+network.json) + `build_displays` + `Coordinator` (GardenState, stale-sender, branch math) | main.py, visualizer.py (TYPE), osc_server.py (TYPE), 3 tests | P |
| `osc_server.py` | 78 | python-osc dispatcher → Coordinator setters | main.py | P |
| `location_sender.py` | 158 | Garden State → ESP32 controllers, change+heartbeat gating | main.py, coordinator.py, test | P (receivers ignore it per ADR-0021) |
| `visualizer.py` | 199 | FastAPI WS (`/ws`, `/logs`) + 7 `/control/*` endpoints | main.py | P |
| `pico_driver.py` | 55 | JSON-lines pixel sink over USB serial | main.py | **P-inert** (see §2) |
| `branch_controller.py` | 49 | JSON-lines servo commands over USB serial | main.py | P |
| `displays/__init__.py` | 24 | re-exports | coordinator, main, tests | P |
| `displays/base.py` | 78 | `ShowMode`, `Color`, `ChannelFrame`, `GardenState`, `Controllable`, `LEDControllable` | all TreeHouse modules | P |
| `displays/led.py` | 119 | generic `LEDDisplay` (6 patterns; ignores GardenState) | coordinator.py | P-inert |
| `displays/effect.py` | 133 | `ForgeAndFloraDisplay` two-strip crossfade | coordinator.py, test | P-inert |
| `displays/video.py` | 87 | `LookingGlassDisplay` → OSC to renderer every frame | coordinator.py | P |
| `displays/porch_lights.py` | 108 | blow-up/aftermath state machine | coordinator.py | P-inert |
| `looking_glass/renderer.py` | 140 | pygame+moderngl shader subprocess, OSC :9002 | main.py (subprocess) | P |
| `looking_glass/{bloom,fractal,mycelium,cosmos}.glsl` | 31/35/72/59 | shaders | renderer.py | P |
| `looking_glass/__init__.py` | 0 | enables `python -m looking_glass.renderer` | — | P |
| `looking_glass/deploy/looking_glass.service` | 26 | **self-declared OBSOLETE** (ADR-0018) | — | X |
| `looking_glass/deploy/install.sh` | 33 | duplicate of `deploy/install.sh` apt/pip steps | — | X |
| `club_screen.py` | 281 | pygame text-rotation subprocess (ADR-0017) | main.py (subprocess) | P |
| `club_messages.txt` | 549 | message content | club_screen.py | P |
| `settings.json` | 126 | see §6 — ~25 lines unread | coordinator.py, club_screen.py | P |
| `requirements.txt` | 7 | python-osc pyserial moderngl numpy uvicorn fastapi pygame | — | P (`numpy` imported nowhere in TreeHouse) |
| `deploy/treehouse.service` | 29 | systemd unit (weston env) | deploy/install.sh | P |
| `deploy/install.sh` | 52 | apt weston/seatd + pip + unit | scripts | P |
| `deploy/weston.ini` | 17 | dual-output compositor config | main.py | P |
| `test_branch_positions.py` | 76 | branch math | — | D |
| `test_dead_sender.py` | 163 | stale-sender zeroing (ADR-0007) | — | D (valid, tests live code) |
| `test_forge_and_flora.py` | 114 | F&F reactivity | — | D (tests inert code) |
| `test_location_sender.py` | 191 | sender gating + config resolution | — | D |

### ShowControl/Dashboard/ (1,019 LOC)

| File | LOC | Purpose | Class |
|---|---|---|---|
| `serve.py` | 117 | FastAPI static + `POST /api/mode` OSC relay | P |
| `index.html` | 113 | 4 status cards polling `/health` on hardcoded ports 8765/8766/8080/8767 (`index.html:55-60` — duplicates `network.json` `http_port`) | P |
| `treehouse.html` | 255 | WS state + log view + control buttons (2 broken, see §0) | P |
| `flowerbeds.html` / `fundingcaptcha.html` | 59/59 | iframe + `/logs` WS — near-identical | P |
| `playingthepipes.html` | 21 | stub | P |
| `dashboard.css` | 332 | styles | P |
| `deploy/dashboard.service`, `deploy/install.sh` | 18/38 | unit + installer | P |
| `requirements.txt` | 7 | fastapi uvicorn python-osc pydantic | P |

Note: no page in the Dashboard actually calls `POST /api/mode` (grep `api/mode` in `*.html` → none).
The only mode control in the UI is `treehouse.html`'s direct POST to the TreeHouse visualizer
(`/control/show/mode`), with the wrong vocabulary. `serve.py`'s relay endpoint is reachable only
by curl.

### ShowControl/OSCFabric/ (314 LOC)

| File | LOC | Purpose | Importers | Class |
|---|---|---|---|---|
| `__init__.py` | 4 | exports | FlowerBeds main.py, FundingCAPTCHA app.py | P |
| `config.py` | 20 | `load_network_config()` | same | P |
| `client.py` | 76 | `FabricClient` (change+heartbeat, one target) | same | P |
| `test_client.py` | 214 | **pytest tests** (20 tests). Despite the name it is not a manual tool. Tests `send_event("game_started")` which no Element sends. | — | D |

### ShowControl root

`network.json` (27 LOC) — P. Keys: `_comment`, `lan`, `heartbeat_interval_s`, `change_epsilon`,
`elements{4}`, `firmware{8}`. No other root-level files.

### scripts/ (617 LOC), Makefile, pytest.ini, .github/

| File | LOC | Purpose | Class |
|---|---|---|---|
| `scripts/deploy.sh` | 79 | laptop → show machine push + `install.sh` | O |
| `scripts/bootstrap-deploy.sh` | 53 | one-time receive.denyCurrentBranch + sudoers | O |
| `scripts/install-services.sh` | 63 | loops per-element `deploy/install.sh` | O |
| `scripts/install-git-hooks.sh` | 20 | symlinks `scripts/git-hooks/*` | D |
| `scripts/git-hooks/pre-commit` | 120 | private-content guard | D |
| `scripts/test_git_hooks.py` | 149 | tests for pre-commit | D |
| `scripts/hooks/smoke_test.py` | 23 | **stub that exits 0**; referenced only by `architecture.md:23`; no `.claude/settings.json` in repo wires it | X |
| `scripts/hooks/firmware_config_gen.py` | 110 | network.json → `TreeHouse_Controllers/include/net_config.h`; FlowerBeds `config.h` is a TODO | O |
| `Makefile` | 5 | `node --test` (0 tests) + `python3 -m pytest \|\| test $? -eq 5` | D |
| `pytest.ini` | 2 | `testpaths = ShowControl IIVision scripts` | D |
| `requirements-dev.txt` | 9 | pytest numpy scipy python-osc fastapi httpx uvicorn pygame moderngl (no `pyserial` — TreeHouse tests avoid importing `main.py`) | D |
| `.github/workflows/tests.yml` | 74 | PR-only: setup node/python, pip dev reqs, apt headless GL, private-content diff guard, `make test` | D |
| `.github/workflows/claude.yml` | 50 | `@claude` mention bot | D |

---

## 2. Dead code

### Confirmed dead (nothing references it)

| Item | Location | LOC | Evidence |
|---|---|---|---|
| `OrbbecRGBCamera`, `RGBFrame`, `cv2` import, section headers | `IIVision/camera.py:30-33, 38-53, 303-425` | ~140 | grep `OrbbecRGBCamera\|RGBFrame` outside IIVision → 0 hits. Comment at `camera.py:39,304` says "used exclusively by the layout calibrator" — deleted by ADR-0015. `cv2` not in any requirements. Also exported from `__init__.py:18,34-35`. |
| Unused imports | `camera.py:19` (`struct`), `:23` (`contextmanager`), `:91` (`OBAlignMode`); `FlowerBeds/main.py:39-48` (`Attraction`, `ClusterConfig`, `ControllerConfig`, `ModuleConfig`); `FlowerBeds/visualizer.py:18` (`Any`); `TreeHouse/pico_driver.py:6` (`Color`); `Dashboard/serve.py:14` (`sys`); tests: `test_layout_tool.py:5-6`, `test_branch_positions.py:2`, `test_detect_foreground.py:5` | ~12 | pyflakes |
| `ControllerConfig` | `FlowerBeds/flower_beds.py:128-135` | 8 | imported by main.py but never instantiated; hardcodes `192.168.1.50:9000` (constraint #3 violation) |
| `_get_loop()` | `FlowerBeds/visualizer.py:377-382` | 6 | 0 callers; pyflakes also flags useless `global _loop` at :378 and :415 |
| `calibration_state` | `FlowerBeds/main.py:222-223, 274` | 3 | always the literal `"calibrated"`; `docs/FlowerBeds.md:146` tells operators to check it |
| `TrackState`/`PreStabilizeFilter` exports | `IIVision/__init__.py:15-16, 26, 30` | 2 | `TrackState` used only inside IIVision + its test; `PreStabilizeFilter` alias unused outside (flower_beds.py:353 redefines the Callable) |
| `Blob3D.cam_half_extents_m`, `.median_z_m`, `.sample_count` | `IIVision/blob_tracker.py:81-83, 429-431` | 6 | computed, never read anywhere |
| `Calibration.delete()` | `blob_tracker.py:138-141` | 4 | only mention is the module docstring at `pipeline.py:16` |
| `CalibrationConfig` | `blob_tracker.py:47-49` | 3 | only ever default-constructed (`:158`); no caller passes one |
| `looking_glass/deploy/looking_glass.service` | 26 | self-described OBSOLETE | git history is the "reference" |
| `looking_glass/deploy/install.sh` | 33 | duplicates `deploy/install.sh:18-30`; adds `usermod -aG _seat` that the live installer lacks (see §8) |
| `scripts/hooks/smoke_test.py` | 23 | stub; `_ = data.get(...)`; nothing invokes it | |
| `.gitignore:17` `layout_calibrated.json` | 1 | file removed by ADR-0015 | |
| `/control/forge-mode` endpoint | `TreeHouse/visualizer.py:108-113` + `Dashboard/treehouse.html:64-69` | ~15 | calls nonexistent `Coordinator.set_forge_mode`; and even `ForgeAndFloraDisplay.set_mode/set_blend` (`effect.py:51-59`) are overwritten every frame by `update()` at `effect.py:79`, so the whole control path is a no-op by design since ADR-0008 |
| `ForgeAndFloraDisplay.set_mode`, `set_blend`, `set_transition_speed`; `LookingGlassDisplay.set_speed`, `set_mirror_depth`; `LEDDisplay.set_color`, `set_brightness`; `Controllable.enable/disable` (only `disable()` called, in a test) | `effect.py:51-62`, `video.py:57-61`, `led.py:49-53`, `base.py:58-62` | ~30 | no callers |
| `Coordinator.get(name)` | `coordinator.py:412-413` | 2 | no callers |
| FlowerBeds `requirements.txt:6` `aiofiles` | 1 | imported nowhere in repo |
| TreeHouse `requirements.txt` `numpy` | 1 | not imported in TreeHouse (ADR-0018 explicitly removed it from the renderer) |

### Config keys nothing reads — see §6 (≈25 lines in TreeHouse/settings.json).

### Live-but-inert: the TreeHouse Pico/Python LED path (decision required)

Evidence the path is superseded in practice, not just on paper:
- ADR-0020 (Sep 2026): "Pi Pico path … stays in the tree until the ESP32-S3 hardware is
  physically installed, then is removed along with `pico_driver.py` and the `pico_*` blocks".
- ADR-0021 (Oct 2026): five ESP32 controllers built incl. Garage; they *ignore* Garden State.
- `Firmware/Club_Pico`, `HouseSwarming_Pico`, `Fungi_Pico` (2026-05-29) are each "standalone Pico
  light controller (stopgap) … no host" — i.e. the dioramas were lit at the show *without* the
  Pi pipeline.
- The Pi code can't drive the documented hardware anyway: single `PicoDriver`
  (`main.py:149`), config key mismatch (`coordinator.py:177` reads `pico`; settings has
  `pico_dioramas`/`pico_structure`), pin collisions (settings `dioramas[0].pico_pin=0` vs
  `dormer.pico_pin=0`; `dioramas[1]=1` vs `porch_lights=1`).
- `displays/led.py:60-63` `LEDDisplay.update()` ignores `state` entirely — ADR-0008's
  `GardenStateResponse` was never built. Only `ForgeAndFloraDisplay` and `PorchLightsDisplay`
  react to GardenState.

If killed: `pico_driver.py` (55), `displays/led.py` (119), `displays/effect.py` (133),
`displays/porch_lights.py` (108), `LEDControllable`/`ChannelFrame`/`Color`/`scale_color` in
`base.py` (~25), `DioramaConfig`/`DormerConfig`/F&F/porch config + loading + `build_displays`
LED branches in `coordinator.py` (~130), `get_all_frames`/`_led_displays`/`set_display_pattern`/
`reset_porch_lights`/`_porch_lights` (~25), `test_forge_and_flora.py` (114), Dashboard LED/forge/
porch controls in `treehouse.html` (~60 + `visualizer.py` endpoints ~30), `Firmware/TreeHouse_PicoLEDs`,
settings blocks (~70 lines). **≈ 800 LOC Python/JS + firmware.** Keep `GardenState`,
`Controllable`, `LookingGlassDisplay`, branch logic, `LocationSender`.

If kept: fix the three bugs above, implement two drivers, and say so in ADR-0020.

### "Display" → "Controllable" rename status (CONTEXT.md:139,143 says "old name — being replaced")

Half-done since 2026-05-22. Base classes are `Controllable`/`LEDControllable` (`base.py:51,73`),
but every concrete class is still `*Display` (`LEDDisplay`, `ForgeAndFloraDisplay`,
`LookingGlassDisplay`, `PorchLightsDisplay`), the package is `displays/`, and `Coordinator` uses
`_displays`, `display_names`, `set_display_pattern`, `build_displays`. ADR-0006's "each room becomes
its own class (`HouseSwarmingDisplay`, `ClubDisplay`, `AtticDisplay`)" never happened — rooms are
rows in `settings.json.dioramas` fed to one generic `LEDDisplay`. ADR-0006 also says
`BranchController` inherits `Controllable`; it doesn't (`branch_controller.py:9` is a plain serial
driver; branch math lives in `Coordinator._update_branch_positions`, `coordinator.py:453-467`).

### `club_screen.py`
Live (subprocess from `main.py:193`), but reads `settings.json.club_screen.{font_size_max,
font_size_min, hold_top_seconds, scroll_speed_px_per_sec, hold_bottom_seconds,
fade_duration_seconds, messages_file}` (`club_screen.py:166-171,243`) while `settings.json:104-107`
provides `interval_seconds` (unread) and `messages_file` only. ADR-0017's "configurable timer
(`interval_seconds`)" was replaced by a fade/hold/scroll state machine without updating ADR or
settings. Also hardcodes `WIDTH, HEIGHT = 800, 480` and `_load_config()` ignores `--config`
(always `./settings.json`).

### `location_sender.py` / `test_dead_sender.py`
Both live and tested. `LocationSender` is the only current Pi→lights link (receivers ignore it,
ADR-0021). `test_dead_sender.py` tests `Coordinator._expire_stale_senders` — live code, but it
asserts on private attrs (`c._flowerbeds_activity`). Note `LocationSender._should_send_float`
(`location_sender.py:129-148`) re-implements `FabricClient.report/tick` semantics
(`OSCFabric/client.py:39-56`) — duplication, see §3.

### `IIVision/pipeline.py`, `transforms.py`
All public functions are called (`filter_positions_near_points` ← flower_beds.py:16;
`build_calibration`/`run_pipeline` ← main.py; all five transforms used). No dead functions here.

### OSCFabric `test_client.py`
It is a pytest module (20 tests, pytest fixtures, `SpyTransport`). Not a manual tool. Its
docstring (`:4`) still says "Red-green-refactor" which is a process note, not documentation.

---

## 3. Duplication

### 3a. FastAPI WebSocket broadcast + log streaming (FlowerBeds vs TreeHouse)

Byte-for-byte duplicates:
- `WebSocketLogHandler`: `FlowerBeds/visualizer.py:319-334` ≡ `TreeHouse/visualizer.py:45-60`
- `/ws` endpoint: `FlowerBeds/visualizer.py:347-358` ≡ `TreeHouse/visualizer.py:130-140`
- `/logs` endpoint: `FlowerBeds/visualizer.py:361-374` ≡ `TreeHouse/visualizer.py:143-156`
- `/health`: `FlowerBeds/visualizer.py:342-344` ≡ `TreeHouse/visualizer.py:67-69` ≡ `Dashboard/serve.py:49-51`
- module globals `app`, `CORSMiddleware(allow_origins=["*"])`, `_connections`, `_log_queues`,
  `_loop`: `FlowerBeds/visualizer.py:312-316` ≡ `TreeHouse/visualizer.py:32-37`
- fan-out loop with dead-socket pruning: `FlowerBeds/visualizer.py:393-404` ≡ `TreeHouse/visualizer.py:174-184`
- uvicorn.Config(..., log_level="warning", loop="asyncio"): `FlowerBeds:424`, `TreeHouse:195`, `layout_tool.py:242`, `serve.py:113`

Differences are only threading model (FlowerBeds runs uvicorn in a daemon thread and bridges via
`run_coroutine_threadsafe`; TreeHouse is already asyncio) and the logger name.

Dashboard HTML duplicates: `flowerbeds.html` ≡ `fundingcaptcha.html` except iframe URL/port
(`:28-30`), and the `appendLog`/`connectLogs` JS block (`flowerbeds.html:36-56`) is repeated in
`treehouse.html:226-250`, `fundingcaptcha.html`.

**Proposal:** `ShowControl/ShowWeb/` package (name chosen to sit beside `OSCFabric`):
```
ShowControl/ShowWeb/__init__.py
ShowControl/ShowWeb/live.py
    class LiveServer:
        def __init__(self, logger_name: str, port: int, html: str | Path | None = None,
                     extra_routes: Callable[[FastAPI], None] | None = None)
        def start_in_thread(self) -> None          # FlowerBeds (sync frame loop)
        async def serve(self) -> None              # TreeHouse (asyncio frame loop)
        def broadcast(self, payload: dict) -> None # thread-safe; no-op when no clients
        async def broadcast_async(self, payload: dict) -> None
    # provides /health, /ws, /logs, optional GET / ; attaches WebSocketLogHandler to logger_name
ShowControl/Dashboard/log-panel.js                 # shared appendLog/connectLogs; pages <script src>
```
Removes ≈110 LOC from each visualizer and ~40 JS lines ×3.

### 3b. Loading `network.json` — four implementations

| Site | Path logic |
|---|---|
| `OSCFabric/config.py:8,13-20` `load_network_config()` | `Path(__file__).parent.parent / "network.json"` |
| `TreeHouse/coordinator.py:169-175` | `Path(settings).resolve().parent.parent / "network.json"` (relative to the *settings file*, so `--config /tmp/x.json` silently loses network.json and logs a warning) |
| `Dashboard/serve.py:23-24,34-37` `_load_network()` | `DIR.parent / "network.json"` |
| `FlowerBeds/layout_tool.py:43,50-52` | `parents[1] / "network.json"` + generic `_load_json` |

Plus the `try: load_network_config() except FileNotFoundError: warn; network = {}` block copied
three times inside `FlowerBeds/main.py:124-128, 301-305, 358-362`.

**Proposal:** everyone imports `OSCFabric.load_network_config`; add
`load_network_config_or_empty(log) -> dict` for the warn-and-continue case; TreeHouse should
stop deriving the path from `--config`.

### 3c. "flowerbeds_controller_*" discovery — three copies

- `FlowerBeds/main.py:74-81` `_build_controllers`
- `FlowerBeds/main.py:92-97` inside `_diagnose_controllers`
- `FlowerBeds/layout_tool.py:55-61` `_flowerbeds_controllers` (+ `_osc_clients:64-68`, `_send_osc:71-75`)

And `/cg/ff/rot` fan-out + yaw negation is in `flower_beds.py:164-167` (`MotorCommand.to_osc_args`)
*and* `layout_tool.py:71-75` (`osc_deg = -deg_software`), with `_OSC_ADDRESS = "/cg/ff/rot"`
defined in both `main.py:56` and `layout_tool.py:31`.

**Proposal:** `ShowControl/FlowerBeds/controllers.py`:
```
OSC_ROT_ADDRESS = "/cg/ff/rot"
@dataclass(frozen=True) class Controller: name, ip, port
def controllers_from_network(network: dict) -> list[Controller]
class ControllerBus:                       # wraps N SimpleUDPClient
    def __init__(self, controllers, enabled=True)
    def send(self, commands: Iterable[MotorCommand]) -> None
    def diagnose(self, expected_motor_ids: set[int]) -> list[int]   # moves _diagnose_controllers here
```
main.py's three run modes and layout_tool both use it; `diag.py` stays as the wire-format module.

### 3d. Change-epsilon + heartbeat gating — two implementations

`OSCFabric/client.py:39-56` (`FabricClient.report/tick`, single target, time via `tick(dt)`) vs
`TreeHouse/location_sender.py:129-148` (`_should_send_float/_should_send_string/_heartbeat_due/_mark`,
N targets, wall clock). Same ADR-0007 rule. `FabricClient` also has a latent bug the sender
avoided: `report()` of an unchanged value never refreshes `_elapsed`, and `tick()` resends *every*
signal when any heartbeat is due (acceptable) — but it has no per-signal timing and no string
support.

**Proposal:** `OSCFabric/gate.py`:
```
class SignalGate:
    def __init__(self, heartbeat_interval_s: float, change_epsilon: float, clock=time.monotonic)
    def due(self, key: str, value: float | str) -> bool      # change or heartbeat
    def mark(self, key: str, value) -> None
```
`FabricClient` and `LocationSender` both become thin wrappers over `SignalGate` + a transport list.

### 3e. Signal-handler / run-forever boilerplate in FlowerBeds/main.py

`_running` flag + `_stop` closure + `signal.signal(SIGINT/SIGTERM)` appears at
`main.py:198-206`, `331-338`, `388-395`. Settings load + network load + `CoordinatorConfig.from_dict`
+ motor-id collection appears at `main.py:123-128,159-164`, `300-314`, `357-370`.

### 3f. TreeHouse config dataclass mirroring

`coordinator.py:86-105` `DioramaConfig`/`DormerConfig` duplicate `displays/led.py:10-19`
`LEDConfig` field-for-field, then `build_displays` (`coordinator.py:285-307`) copies one into the
other. `TreehouseConfig` (`:108-125`) hand-mirrors settings.json; `load_config` (`:165-275`) is
110 lines of `raw.get(...)`. Replace `DioramaConfig`/`DormerConfig` with `LEDConfig` directly
(−45 LOC) or, better, give each config dataclass a `from_dict` like FlowerBeds'
`_kwargs_from_dict` (`flower_beds.py:24-27`) — a pattern that itself is duplicated by
`StabilizerConfig.from_dict` (`blob_stabilizer.py:34-37`).

### 3g. systemd units and installers — four near-identical copies

`FlowerBeds/deploy/install.sh:30-62`, `TreeHouse/deploy/install.sh:8-52`,
`Dashboard/deploy/install.sh:26-56`, `looking_glass/deploy/install.sh` share: `SCRIPT_DIR/REPO_ROOT`
resolution, `SERVICE_USER="${SUDO_USER:-ii}"`, `pip3 install --break-system-packages -r`,
`sed "s|User=ii|User=$SERVICE_USER|g" unit > /etc/systemd/system/X.service`,
`daemon-reload/enable/restart`, and the "Status/Logs/Viz" echo trailer. The `.service` files share
`Restart=always RestartSec=5 User=ii StandardOutput=journal …` and the hardcoded
`WorkingDirectory=/home/ii/CommunityGarden/ShowControl/<X>`.

**Proposal:** `scripts/lib/install-element.sh` with
`install_element <Element> <service-name> [apt pkgs...]` that does the shared steps; each
`deploy/install.sh` becomes ~8 lines (element-specific apt/symlink steps + the call).
Keep per-element `.service` files but template `WorkingDirectory=` from `REPO_ROOT` in the sed
(bootstrap.md:40 already warns the path is assumed).

---

## 4. Modularization — files >300 LOC

### `ShowControl/TreeHouse/coordinator.py` (485)
Mixes: (a) 9 config dataclasses `:33-125`; (b) settings+network JSON loading `:132-275`;
(c) object factory `build_displays` `:282-311`; (d) `Coordinator` runtime `:318-485`, which itself
mixes Fabric-signal intake + stale-sender policy (`:387-433`), GardenState assembly (`:435-451`),
branch motor math (`:453-471`), and LED frame aggregation (`:473-478`).
Split:
- `config.py` — dataclasses + `load_config` (a, b). ~200 LOC.
- `garden_state.py` — `SignalIntake` class: setters, `_touch`, `_expire_stale_senders`,
  `snapshot() -> GardenState`. ~90 LOC. `test_dead_sender.py` targets this.
- `branches.py` — `BranchMotorConfig` + `branch_positions(motors, state) -> list[(id, deg)]`
  pure function (ADR-0006 wanted a `BranchController(Controllable)` — do that: the serial driver
  and the math in one `Controllable`). `test_branch_positions.py` targets this.
- `coordinator.py` — ~80 LOC: holds `list[Controllable]`, `update(dt)`, `get_all_states`,
  pixel aggregation if the Pico path survives.
- `build_displays` → `displays/factory.py`.

### `ShowControl/FlowerBeds/main.py` (454)
Mixes: config/network loading, camera factory `:130-149`, controller bus + diagnostics `:74-115`,
calibration persistence `:208-223`, the frame loop `:225-285`, visualizer state assembly
`:254-277`, and two standalone motor-calibration CLIs `:292-411` (120 LOC) that share nothing
with the camera path.
Split:
- `controllers.py` (see §3c) — bus + diagnostics. −60.
- `calibrate_motors.py` — `run_calibrate`, `run_calibrate_sweep` as its own entry point
  (`python calibrate_motors.py --hold 0` / `--sweep`); they never touch IIVision. −120.
- `state.py` — `build_visualizer_state(frame, tracked, coordinator, cam_cfg, missing)`; move the
  `*State` TypedDicts here from `visualizer.py:30-60` so `flower_beds.py:21` stops importing from
  the web layer. −30.
- `main.py` becomes CLI + `run()` ≈ 180 LOC.

### `ShowControl/FlowerBeds/visualizer.py` (434)
240 of 434 lines are an HTML/JS string (`:66-305`). Move the client to
`FlowerBeds/visualizer_static/index.html` (the layout tool already uses `StaticFiles` + separate
`index.html/style.css/layout.js`, so the precedent is in the same directory). The remaining ~130
lines of server collapse to ~25 once `ShowWeb.LiveServer` (§3a) exists. ADR-0015's "same pattern
as visualizer.py — embedded HTML" is the pattern to drop, not copy.

### `IIVision/blob_tracker.py` (434)
Three concerns: frame/intrinsics/blob dataclasses `:29-90`; calibration model + builder `:97-216`;
detector `:223-434`. Split into `types.py` (`FramePacket`, `CameraIntrinsics`, `Blob2D`, `Blob3D`,
`DetectionResult`, `DetectionConfig`), `calibration.py` (`Calibration`, `Calibrator`,
`CalibrationConfig`), `detector.py` (`BlobTracker`). Each <220 LOC and each readable alone;
`camera.py` and `silhouette_warp.py` then import only `types`. The class name `BlobTracker` is a
misnomer (it does per-frame detection; tracking is `BlobStabilizer`) — architecture.md:50 even
calls it "per-frame detection". Rename to `BlobDetector` with a one-line alias.

### `IIVision/camera.py` (425)
Delete `OrbbecRGBCamera`/`RGBFrame` (−140 → 285). Then split `orbbec.py` (`OrbbecCamera`,
`_apply_depth_mirror`) and `mock.py` (`MockCamera`); `BaseCamera` protocol goes to `types.py`.
The retry-forever loop in `__enter__` (`:120-134`) is the only logic worth a unit test.

### `ShowControl/FlowerBeds/flower_beds.py` (379)
Under 400 but three concerns: config dataclasses `:34-152` (120 LOC), `Attraction` policy, and
the `FlowerCluster/FlowerModule/Coordinator` runtime. Move config types to `config.py`; the
`snapshot()`/`ClusterState` coupling to the visualizer (`:21, 364-379`) goes with `state.py`.

### `ShowControl/FlowerBeds/layout_tool/layout.js` (569) — operator tool; fine as-is, but
`DEFAULT_OFFSETS` is fetched from `/api/defaults` while the server also hardcodes
`_DEFAULT_CLUSTER_OFFSETS` (`layout_tool.py:34-39`) that contradict ADR-0015 and
`configuration.md` (see §7).

---

## 5. Package structure and imports

### Today
- No `pyproject.toml`, `setup.py`, `setup.cfg`, or `conftest.py` anywhere in the repo.
- `IIVision/` is a package (has `__init__.py`) but is not installable; it is reached by
  `sys.path.insert(0, parents[2])` in `FlowerBeds/main.py:32` and FundingCAPTCHA
  (`app.py:42-44`, `body_blobs.py:28`, `body_grid_tester.py:47-48`).
- `OSCFabric/` is a package reached by `sys.path.insert(0, parents[1])` in `FlowerBeds/main.py:53`
  and `FundingCAPTCHA/app.py:43`. **TreeHouse and Dashboard do not import it at all** — they
  reimplement network loading (§3b).
- Elements are flat script directories without `__init__.py` (`main.py` does `from flower_beds
  import …`, `from coordinator import …`); only `TreeHouse/displays/` and `looking_glass/` are
  packages.
- Tests work because `python -m pytest` puts the cwd (repo root) on `sys.path` (so
  `IIVision.*`, `OSCFabric.*` resolve) and pytest's rootdir-less "prepend" mode puts each test
  file's directory on `sys.path` (so `from coordinator import …` resolves). Bare `pytest` from
  root would still work for most but breaks for `OSCFabric/test_client.py` if run from another
  cwd; `pytest.ini` has no `pythonpath`.
- Dependency lists: three per-element `requirements.txt` + `requirements-dev.txt`, each a
  partial, inconsistent copy (FlowerBeds pins `fastapi>=0.100`, TreeHouse pins nothing; FlowerBeds
  has unused `aiofiles`; TreeHouse has unused `numpy`; `requirements-dev.txt` lacks `pyserial`
  so any test that imports `TreeHouse/main.py` or `pico_driver.py` would fail in CI).
- `architecture.md:40` says "Import from the `IIVision` package directly, not from its internal
  modules" — violated by `flower_beds.py:16-17`, `test_flower_beds.py:7`, `FundingCAPTCHA/body_blobs.py:30`,
  `FundingCAPTCHA/test_silhouette.py:77`.

### Minimal change (one PR)
1. Add `/pyproject.toml`:
   ```toml
   [build-system] requires = ["setuptools>=68"]; build-backend = "setuptools.build_meta"
   [project] name = "communitygarden"; version = "0"; requires-python = ">=3.11"
   dependencies = ["numpy", "scipy", "python-osc"]
   [project.optional-dependencies]
   flowerbeds = ["fastapi>=0.100", "uvicorn[standard]", "pyorbbecsdk2"]
   treehouse  = ["fastapi", "uvicorn", "pyserial", "pygame", "moderngl"]
   dashboard  = ["fastapi", "uvicorn", "pydantic>=2"]
   dev        = ["pytest>=8", "httpx", "pyflakes"]
   [tool.setuptools] packages = ["IIVision", "OSCFabric"]
   [tool.setuptools.package-dir] OSCFabric = "ShowControl/OSCFabric"
   [tool.pytest.ini_options] testpaths = ["ShowControl", "IIVision", "scripts"]
   pythonpath = ["."]
   ```
2. Each `deploy/install.sh`: `pip3 install --break-system-packages -e "$REPO_ROOT[flowerbeds]"`;
   delete the three `requirements.txt`; `requirements-dev.txt` → `pip install -e .[dev,flowerbeds,treehouse,dashboard]` in `tests.yml`.
3. Delete the `sys.path.insert` lines (`FlowerBeds/main.py:31-32, 52-53`; FundingCAPTCHA ones
   belong to the other auditor). TreeHouse `coordinator.py:169-175` and `Dashboard/serve.py:34-37`
   switch to `from OSCFabric import load_network_config`.
4. Element-local imports stay flat (`from flower_beds import …`) — acceptable because each Element
   is run with cwd = its directory (the `.service` files set `WorkingDirectory`). If you want
   `python -m ShowControl.FlowerBeds.main` later, add `__init__.py` to `ShowControl/` and each
   Element and convert to relative imports; not required for the goal.
5. Delete `pytest.ini` and fold into `pyproject.toml`.

Result: a reader can open `IIVision/` or `ShowControl/OSCFabric/` and see exactly what they
depend on; an Element's `pyproject` extra is its full dependency list.

---

## 6. Config

### `ShowControl/network.json` — readers per key
| Key | Read by |
|---|---|
| `lan` | `firmware_config_gen.py:50-54` only |
| `heartbeat_interval_s` | OSCFabric client, TreeHouse coordinator `:160,262` |
| `change_epsilon` | OSCFabric client `:35`, TreeHouse `:161` |
| `elements.*.ip/osc_port` | FlowerBeds main (treehouse only), Dashboard serve, TreeHouse (`treehouse.osc_port` as listen port `:261`) |
| `elements.*.http_port` | **nothing in Python**; Dashboard `index.html:55-60` hardcodes the same four ports instead |
| `firmware.flowerbeds_controller_*` | FlowerBeds main/layout_tool |
| `firmware.treehouse_branch` | **nothing** (all `null`; placeholder) |
| `firmware.treehouse_{swannatopia,julia,jess,dormer,garage}` | TreeHouse `_load_locations`, `firmware_config_gen.py` |
| `firmware.*.mac` | **nothing** (`firmware_config_gen.py` emits IPs only; FlowerBeds firmware hardcodes its own) |
Schema is documented only by example in ADR-0007 / configuration.md / Dashboard.md, and all three
examples are stale (missing `lan`, `change_epsilon`, the five `treehouse_*` entries).

### `ShowControl/TreeHouse/settings.json` (126 lines) — unread keys
| Key | Lines | Status |
|---|---|---|
| `pico_dioramas`, `pico_structure` | 2-10 | **unread** — code reads `pico` (`coordinator.py:177`); falls back to `/dev/ttyACM0` |
| `garage_windows.forge_and_flora.arc_led_count`, `bloom_led_count` | 69, 71 | **unread** — code reads `led_count` (`coordinator.py:208`), default 48, so F&F drives 48 px on 20-px strips |
| `garage_windows.forge_and_flora.flicker_intensity` | 74 | **unread** — code reads `base_flicker_intensity`/`max_flicker_intensity` (`:211-212`) |
| `attic` (whole block) | 95-102 | **unread** — no `attic` anywhere in Python |
| `club_screen.interval_seconds` | 105 | **unread** — `club_screen.py` reads six other keys |
| `looking_glass.mirror_depth`, `speed` | 62-63 | read into state only; `mirror_depth` never sent to renderer (`video.py:73-75`) |
| `_locations_comment` | 17 | comment |
Also: `locations.controllers` includes `treehouse_garage`, correct per ADR-0021.
Schema is undocumented (no section in `docs/agents/configuration.md`, which covers FlowerBeds only).

### `ShowControl/FlowerBeds/settings.json` (848 lines)
All top-level keys are read (`calibration_frames`, `stabilizer`, `coordinator`,
`activity_max_blobs`, `cameras`). Per-cluster `yaw_limit_deg` is absent from every cluster
(defaults 60) although the layout tool writes it for new modules (`layout_tool.py:89`) and
`docs/FlowerBeds.md:29` describes it as present. `cameras[0]._note` and `*._comment` keys are
silently dropped by `_kwargs_from_dict`. `configuration.md:76-84` documents a `serial` camera key
that `CameraConfig` (`flower_beds.py:139-148`) does not have and `main.py:145-148` never passes
to `OrbbecCamera`; `mirror` (which *is* read) is undocumented. 848 lines for 48 clusters because
every 3-vector is pretty-printed one number per line (`json.dump(indent=2)` in
`layout_tool.py:154`) — a compact writer would make it ~200 lines.

---

## 7. Docs drift (claims that are now false)

### AGENTS.md
- `#1` "`IIVision.Blob3D.world_pos_cm()` converts" — no such method; it is `orbbec_to_world()`.
- `#3` "firmware reads a generated `config.h`" — only `TreeHouse_Controllers/include/net_config.h`
  is generated; FlowerBeds `.ino:26` hardcodes `192.168.1.51`.
- "make test runs Node tests (FundingCAPTCHA)" — zero Node tests exist.

### docs/agents/architecture.md
- Repo layout (`:5-25`) omits `ShowControl/PlayingThePipes/`, `Prototypes/`, six of nine
  `Firmware/*` dirs (incl. `TreeHouse_Controllers`, the live one), `scripts/{deploy,bootstrap-deploy,install-services,install-git-hooks}.sh`,
  `scripts/git-hooks/`, `scripts/test_git_hooks.py`, `.github/`, `README.md`, `requirements-dev.txt`.
  Says `pytest.ini # testpaths = ShowControl IIVision` — actual adds `scripts`.
- `:23` lists `smoke_test.py` as a real hook — it is a stub.
- IIVision table (`:31-37`) omits `silhouette_warp.py`; says `blob_tracker.py` has `Blob3D`,
  `FramePacket` but omits `Calibration`/`Calibrator` (in `pipeline.py` row instead — they live in
  `blob_tracker.py:97-216`).
- `:40` "Import from the IIVision package directly" — violated in-repo (§5).
- `:60-67` "`ShowControl/FlowerBeds/layout_tool.py` … see ADR-0015" — fine, but the pipeline
  diagram (`:47-56`) omits `--recalibrate` / `Calibration.load` persistence and the boot
  diagnostics.
- `:104-111` "Visualizer … The Show Dashboard aggregates per-Element visualizers" — true for
  FlowerBeds (iframe) but the Dashboard never calls its own `/api/mode`.

### docs/agents/python-conventions.md
- `:28` `Blob3D.world_pos_cm()` — wrong (see above).
- Module table (`:5-12`) omits `diag.py`, `layout_tool/` directory, `visualizer.py`'s `/logs`.
- `:42-44` "logger `flower_beds` … never `print`" — `visualizer.py:434`, `layout_tool.py:235-237`,
  `Dashboard/serve.py:110-111` use `print`; IIVision logs under `IIVision.*` so calibration
  messages never reach the Dashboard log stream (handler attached only to `flower_beds`,
  `visualizer.py:433`).

### docs/agents/configuration.md
- Camera example has `serial` (unread) and lacks `mirror` (read).
- Default cluster offsets `[40,-30],[40,-75],[100,-25],[95,-70]` (`:30-49`) vs code
  `[30,30],[-30,30],[30,-30],[-30,-30]` (`layout_tool.py:34-39`).
- Says `motor_id` "Default sequential IDs (1–48) are placeholders" — fine.
- network.json example (`:93-108`) missing `lan`, `change_epsilon`, five `treehouse_*` entries.
- Covers only FlowerBeds settings; nothing on TreeHouse `settings.json`.

### docs/agents/running-and-testing.md
- `:5` Node tests claim.
- CLI table (`:33-43`) omits `--recalibrate`, `--calibrate-yaw-sweep`, `--sweep-period-s`
  (present in `main.py:421-437` and in `docs/FlowerBeds.md:87-89`).
- `:60` "Open http://localhost:8765 to verify … camera positions" OK.

### docs/agents/firmware.md
- `:9` FlowerBeds "IP and MAC come from a generated `config.h`" — false (see §0.6).

### docs/TreeHouse.md
- `:11` "2× Pi Pico … Pico A/Pico B" — code supports one `PicoDriver` and reads neither
  `pico_*` key.
- `:116` "Location controllers … Four ESP32-S3" and table `:120-125` — five since ADR-0021
  (Garage, 192.168.1.64 is in `network.json:25` and `settings.json:25`).
- `:181` "Each diorama / structural light is its own subclass with its own GardenState-reactive
  animation" — dioramas and dormer are generic `LEDDisplay` instances whose `update()` ignores
  GardenState (`led.py:60-63`).
- `:185` "captcha_blowup drives the attic-spike Blow-Up Reaction" — no attic code exists; the
  `attic` settings block is unread.
- `:22` "`pico_driver.py` … `branch_controller.py`" reference list fine; `:143-148` udev table
  fine but moot.
- OSC table `:201-210` omits `/lookingglass/scene` also being accepted on :9001
  (`osc_server.py:58`).
- Troubleshooting `:218` "LEDs dark … remove `--no-pico`" — LEDs are now ESP32-driven.

### docs/FlowerBeds.md
- `:103` `/flowerbeds/mode` inbound — no listener exists.
- `:29` per-cluster `yaw_limit_deg` "optional" — true, but none set in shipped settings.
- `:146` tells operators to check `calibration_state` — constant.
- `:78-80` says layout tool POST `/api/aim` sends to "every controller IP" — true; ADR-0015
  says per-controller body — ADR is wrong, not the doc.

### docs/Dashboard.md
- `:14` "Per-Element pages … reflect status" OK; `:16` "`POST /api/mode` relays" — exists but no
  UI calls it, and the TreeHouse page bypasses it with wrong vocabulary.
- network.json example (`:46-61`) stale (no `mac`, `lan`, treehouse entries).
- Troubleshooting `:74` "Mode flip has no effect — Element doesn't listen" — true for FlowerBeds
  today and should say so.

### docs/showtime.md
- `:24-28` Services table: TreeHouse hardware "Picos, branch motor, 2× HDMI" — no ESP32s.
- `:141` TreeHouse no-hardware command lacks `--no-locations`.
- `:119-124` deploy examples OK and match `deploy.sh`.

### docs/bootstrap.md
- `:10` hardware inventory: TreeHouse "2× Pi Pico (USB)" — no ESP32 controllers, no WiFi AP
  requirement for them.
- `:117` "Record the serials in `network.json` under `firmware`" — no such fields exist and
  nothing would read them.

### CONTEXT.md
- `:139,143` "`Display`/`LEDDisplay` — old name, being replaced" — stalled since May.
- `:142` "Two `PicoDriver` instances (one per Pico)" — one in code.
- `:120` "Four dioramas … each its own LEDControllable with distinct animation" — generic.
- `:190-191` Signal Bag "pattern used inside Controllable implementations" — exists only in
  firmware (`Firmware/TreeHouse_Controllers`), not in any Python Controllable.

### ADRs
- **ADR-0001** "addresses configured statically in each Element's `settings.json`" — superseded by
  ADR-0007's `network.json`; not marked amended.
- **ADR-0005** OK (JSON-lines, `/dev/treehouse-branches`).
- **ADR-0006** Consequences: `displays/base.py` refactor done; per-room subclasses not done;
  `BranchController` as `Controllable` not done; `coordinator.py` "splits list[Controllable] /
  list[LEDControllable]" — done via `isinstance` filter. Not marked "partially implemented".
- **ADR-0007** `/captcha/game_started` defined but no sender/receiver (only `test_client.py:107`);
  "Each element needs an OSC listener … new for FlowerBeds" — not done. Dashboard upgrade done.
- **ADR-0008** Branches: "startle/recoil before settling" — recoil applied only on the single frame
  `captcha_blowup` is True (`coordinator.py:456-457`; flag cleared at `:445`), i.e. ~33 ms.
  LookingGlass scene-priority rule + `overload` scene — not done (`video.py:36` has 4 scenes;
  `update()` only sends intensity). `GardenStateResponse` for LEDDisplay — not done. Porch
  lights — done. ForgeAndFlora — done.
- **ADR-0010** "Udev rules are generated by `scripts/install-services.sh` using serial numbers in
  `network.json`" — false (script `:38-48` just loops install.sh; bootstrap.md says do it by
  hand). "`PicoDriver` instantiated twice" — no. "`settings.json` splits pico into
  `pico_dioramas`/`pico_structure`" — settings did, code didn't. `arc_led_count`/`bloom_led_count`
  — settings did, code didn't. Status should be "Superseded by ADR-0020" (0020 says so; 0010's
  own header still says Accepted).
- **ADR-0015** "Single file … embedded HTML/JS (same pattern as visualizer.py)" — implemented as
  `layout_tool/` static dir. Endpoint table omits `/api/defaults`; `/api/aim` body documented as
  `{motor_id, deg, controller_ip, osc_port}` vs actual `{motor_id, deg}` broadcast to all.
  Default offsets table differs from code. "Hold at ___°" at 2 Hz — `layout.js:452-477` exists
  (ok). Phase 3 docs tasks were only partly done (configuration.md still shows old offsets).
- **ADR-0017** `treehouse/club_screen.py` path prefix wrong (it's `ShowControl/TreeHouse/`);
  `interval_seconds` key not read; "scanline every 2px" vs `SCANLINE_THICKNESS_PX = 4`; "ACID HOUSE
  FOREVER" examples fine.
- **ADR-0018** says `weston.ini` lives in `looking_glass/deploy/` with `shell=kiosk-shell.so`;
  actual `deploy/weston.ini` uses `shell=desktop-shell.so` (`weston.ini:3`). "`install.sh` installs
  weston" — both installers do; the LG one should be deleted.
- **ADR-0020** "four locations" — five after 0021 (0020 header notes the amendment, body tables
  don't). Pico removal promise outstanding.
- **ADR-0021** consistent with code/firmware; `location_sender.py` sends to Garage (ok).
- **ADR-0002, 0009** fine.

---

## 8. Scripts / CI consistency

- `scripts/deploy.sh:74-78` runs `sudo bash /home/ii/CommunityGarden/ShowControl/$element/deploy/install.sh`;
  `scripts/bootstrap-deploy.sh:45` grants NOPASSWD on `$REPO_ROOT/ShowControl/*/deploy/install.sh`
  via both `/bin/bash` and `/usr/bin/bash`; `scripts/install-services.sh:38-47` loops the same
  scripts as root. Consistent with each other and with showtime.md/bootstrap.md. Hardcoded
  `/home/ii/CommunityGarden` in `deploy.sh:76,78` and all four `.service` files; `bootstrap-deploy.sh`
  derives `REPO_ROOT` dynamically — so a non-default clone path works for sudoers but not for
  deploy.sh or the units.
- `install-services.sh:19` `ALL_ELEMENTS=(FlowerBeds TreeHouse Dashboard FundingCAPTCHA)` — fine
  (Pipes is Windows). Service-name list `:53` matches units.
- **Seat permission inconsistency:** `treehouse.service:16` sets `LIBSEAT_BACKEND=seatd`, which
  requires the service user in group `_seat`; `TreeHouse/deploy/install.sh` never adds it
  (`SupplementaryGroups=dialout` only, `:23`), while the obsolete `looking_glass/deploy/install.sh:20`
  does `usermod -aG _seat`. Either the live installer is missing a step or the Pi was provisioned by
  the dead script.
- Stale comments: `flowerbeds.service:6-7` ("Remove `--no-osc`/`--no-visualizer`") — neither flag
  is in `ExecStart:11`; `treehouse.service:6-7,22` ("Add `--no-pico`", "Pico appears as
  `/dev/ttyACM0`") — stale vs udev symlinks.
- `FlowerBeds/deploy/install.sh:43` apt-installs `python3-numpy python3-scipy` then pip-installs
  `numpy>=1.24 scipy>=1.10` from requirements, which may replace them with wheels anyway.
- `.github/workflows/tests.yml` runs on `pull_request` only (no `push` to main), installs
  `requirements-dev.txt` + headless GL (for FundingCAPTCHA shader tests), runs the private-content
  guard, then `make test`. `make test` = `node --test` (0 tests, exits 0) + `python3 -m pytest ||
  test $? -eq 5`. So CI == `make test` == pytest. `requirements-dev.txt` lacks `pyserial` and
  `pydantic` pin — fine today only because no test imports `TreeHouse/main.py`/`pico_driver.py`/
  `branch_controller.py`; `Dashboard/serve.py` has no tests at all.
- `scripts/hooks/firmware_config_gen.py` is both a Claude hook (stdin JSON) and a CLI; the hook
  mode is undocumented outside its docstring and nothing in the repo wires it (`.claude/` is
  gitignored). `smoke_test.py` is a no-op stub.
- `scripts/test_git_hooks.py` + `pre-commit` are solid and tested (11 tests).

---

## 9. Deletable LOC estimate

| Bucket | LOC | Confidence |
|---|---|---|
| IIVision `OrbbecRGBCamera`/`RGBFrame`/cv2 + unused imports/exports | ~150 | certain |
| `looking_glass/deploy/*` | 59 | certain |
| `smoke_test.py` | 23 | certain |
| FlowerBeds: `ControllerConfig`, unused imports, `_get_loop`, `calibration_state`, dead requirements | ~25 | certain |
| TreeHouse: unused setters/`get()`/`enable()`, `DioramaConfig`/`DormerConfig` collapse, broken forge-mode endpoint + UI | ~110 | certain |
| TreeHouse settings.json unread keys | ~25 | certain |
| Duplication removable via `ShowWeb.LiveServer`, `OSCFabric.load_network_config` reuse, `SignalGate`, `controllers.py`, shared installer | ~350 | high |
| FlowerBeds visualizer HTML → static file (moves, not deletes; Python file −240) | 240 moved | high |
| **Subtotal, no hardware decision** | **≈ 740 LOC** | |
| TreeHouse Pico/LED pipeline + its tests + Dashboard LED UI + `Firmware/TreeHouse_PicoLEDs` | ~800 | needs product decision (ADR-0020 already promised it) |
| **Total if Pico path is retired** | **≈ 1,500 LOC** (~25% of in-scope Python) | |

---

## 10. Top refactors, ranked by value / effort

1. **Fix the three live breakages (½ day):** add `/flowerbeds/mode` listener to FlowerBeds
   (reuse TreeHouse `osc_server.py` pattern), fix `treehouse.html` mode strings to
   `active/dim/inactive`, delete `/control/forge-mode` (or implement `Coordinator.set_forge_mode`).
   Then correct AGENTS.md #1 and #3 and firmware.md so the agent instructions stop lying.
2. **Decide and execute the TreeHouse Pico retirement (1 day):** per ADR-0020's own plan. Removes
   ~800 LOC and three config bugs, collapses `coordinator.py` to ~150 LOC, and makes `displays/`
   honest (`Controllable`, `GardenState`, `LookingGlassDisplay`, branches). Finish the
   `Display→Controllable` rename at the same time (it becomes a 4-file rename).
3. **Packaging (½ day):** root `pyproject.toml` with `IIVision` + `OSCFabric` as installable
   packages and per-element extras; delete `sys.path` hacks and the three `requirements.txt`; make
   TreeHouse and Dashboard import `OSCFabric.load_network_config`. Unlocks reading any one package
   in isolation.
4. **`ShowWeb.LiveServer` + static HTML (1 day):** dedupe the two visualizers and Dashboard pages;
   move FlowerBeds' 240-line HTML string into a file. Both visualizers drop to <60 LOC of Python.
5. **Split `IIVision/blob_tracker.py` and `FlowerBeds/main.py` (1 day):** `types/calibration/detector`;
   `controllers.py` + `calibrate_motors.py` + `state.py`. Add the missing tests for `Calibrator.build`
   and `BlobTracker.detect` while touching them — the production CV path currently has none.

Then: regenerate `architecture.md` repo layout from `tree`, add a TreeHouse section to
`configuration.md`, mark ADR-0001/0006/0008/0010/0017/0018 with status lines reflecting what was
actually built, and delete `.gitignore:17`.
