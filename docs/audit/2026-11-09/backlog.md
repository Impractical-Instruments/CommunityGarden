# Audit backlog — 2026-11-09

Each item is sized to be one PR and one issue. Effort: **S** ≤ half day, **M** ≈ 1 day, **L** 2–3 days. All six decisions in [README §5](README.md#5-decisions-made-2026-11-09) were made on 2026-11-09; the "Gate" column records which decision each item depended on. Nothing is gated now. "Source" points at the section of the detail report with the evidence. Paths are repo-relative; `FC/` = `ShowControl/FundingCAPTCHA/`, `TH/` = `ShowControl/TreeHouse/`, `FB/` = `ShowControl/FlowerBeds/`.

Run `make test` before and after every item; it must stay at 303 passed. Items that delete tests say so.

---

## Phase 0 — Delete and fix (no design decisions unless gated)

| ID | Task | Effort | Gate | Source |
|---|---|---|---|---|
| P0-01 | Tag and delete `Pipes Prototype 3/` | S | — | firmware §3b, §3c |
| P0-02 | Collapse `MakeNoiseDay/` into `Lamplight2026/` | S | — | firmware §3b |
| P0-03 | Prune `Lamplight2026/media/` | S | D4 ✓, D6 ✓ | firmware §3d |
| P0-04 | Delete `docs/superpowers/`, `docs/PRD.md`, `docs/games/`, two template docs | S | — | docs §1, §5, §6 |
| P0-05 | Delete `Prototypes/`; move 2 fabrication READMEs | S | — | firmware §2 |
| P0-06 | Delete `Club_Pico`, `HouseSwarming_Pico`, `Fungi_Pico` | S | — | firmware §1a |
| P0-07 | Untrack `.vscode` cache; add PlatformIO ignores | S | — | firmware §1e, §5 |
| P0-08 | Fix `_save_local({})` bug | S | — | fundingcaptcha §2 |
| P0-09 | Delete unloaded Keepaway game and its data | S | D5 ✓ | fundingcaptcha §2 |
| P0-10 | Delete FundingCAPTCHA dead members | S | — | fundingcaptcha §2 |
| P0-11 | Delete `FC/distribution/` and the `sys.frozen` branch | S | D2 ✓ | fundingcaptcha §2 |
| P0-12 | Delete dead IIVision RGB camera + unused exports | S | — | core §2 |
| P0-13 | Delete core dead code (`looking_glass/deploy/`, `smoke_test.py`, setters, `ControllerConfig`…) | S | — | core §2 |
| P0-14 | Retire TreeHouse Pico LED path per ADR-0020 | M | D1 ✓ | core §2 "Live-but-inert", firmware §1b |
| P0-15 | Fix Dashboard→TreeHouse controls | S | — | core §0.2 |
| P0-16 | Remove the 5 unimplemented OSC addresses | S | D3 ✓ | core §0.3, docs §2 ADR-0007 |
| P0-17 | Fix AGENTS.md: constraint #1 function name, constraint #3 claim, Node tests; drop `node --test` from Makefile | S | — | docs §2 AGENTS.md |
| P0-18 | Fix TreeHouse `settings.json` unread keys | S | D1 ✓ | core §6 |
| P0-19 | Delete 16 unreferenced LFS images | S | — | fundingcaptcha §1 |

### P0-01 Tag and delete `Pipes Prototype 3/`
- **Why:** 110 files, 133,349 lines, 6.8 MB tracked (64% of repo bytes), 112 MB LFS. Transitive reachability from `Lamplight2026.maxpat` over bpatcher names and object text reaches nothing in it. Ten `.amxd`/`.maxpat` pairs are byte-identical apart from a 20-byte header. Its 24 media files are byte-identical to Lamplight2026's.
- **Do:** `git tag archive/pipes-prototype-3 56de83c && git push origin archive/pipes-prototype-3`; `git rm -r "ShowControl/PlayingThePipes/Pipes Prototype 3"`.
- **Done when:** directory gone; tag on remote; `docs/PlayingThePipes.md` does not mention it.

### P0-02 Collapse `MakeNoiseDay/` into `Lamplight2026/`
- **Why:** Vendored personal Max library (own MIT LICENCE + README with streaming links). Lamplight2026 uses exactly two files via `knobgrain.maxpat`: `scaleclip.maxpat`, `wakemove.maxpat`. `Lamplight2026.maxproj:20-40` pins three MakeNoiseDay deps by `~/Projects/...` absolute bootpath; one (`autograin`) is referenced by nothing.
- **Do:** copy the two patchers into `Lamplight2026/patchers/`; remove the three `singleton.bootpath` entries from the `.maxproj`; delete `MakeNoiseDay/` (24 files, 16,178 lines). Open the project in Max once to confirm it resolves.
- **Done when:** `Lamplight2026.maxproj` has no path outside its own folder; `MakeNoiseDay/` gone.

### P0-03 Prune `Lamplight2026/media/` — D4: keep all; D6: LFS stays
- **Why:** 33 LFS files, 114 MB. 20 files (41 MB, incl. `tone.04.wav` 22 MB) are named by no patcher. Max can load buffers by message at runtime, so static grep is necessary but not sufficient.
- **Decided:** keep all Lamplight2026 media in LFS. Only the Prototype 3 duplicates go (P0-01). `grainflow.wav` is referenced but absent from `media/`; confirm it is a Grainflow package sample.
- **Done when:** P0-01 is done; nothing further.

### P0-04 Delete planning artefacts and template docs
- **Why:** `docs/superpowers/` is 13 files / 4,328 lines (46% of all doc lines) of AI pair-programming transcripts; all five features are shipped and tested. `docs/PRD.md` is a May-2026 pre-festival snapshot. `docs/games/rhythm.md`, `upsidedown.md` describe code deleted in May; `bodycaptcha.md`/`bodygrid.md`/`keepaway.md` are stale (hold "resets" vs drains, progress bar vs ring, wrong module path, wrong `update()` signature). `docs/agents/domain.md` and `triage-labels.md` are unmodified third-party templates referencing files that do not exist here.
- **Do:** `git rm -r docs/superpowers docs/games docs/PRD.md docs/agents/domain.md docs/agents/triage-labels.md`. Salvage five one-liners into `common.glsl` headers (list in docs §5). Fix inbound links: `docs/FundingCAPTCHA.md:61`, `docs/adr/0022…:1448`. Put the Rhythm/UpsideDown port in one GitHub issue if still wanted. Fold the 5-line label table into `git-workflow.md`.
- **Done when:** `grep -r superpowers docs` is empty; `make test` unchanged.

### P0-05 Delete `Prototypes/`
- **Why:** 14 TouchTest symbols and 3 ForgeAndFlora symbols have zero hits in `ShowControl/`+`IIVision/`. `TH/test_forge_and_flora.py` tests production `displays/effect.py`, not the prototype. GlowPanels' two build READMEs are the fabrication record of the shipped Mycelium panel (`NUM_LEDS=224` matches settings).
- **Do:** move `Prototypes/GlowPanels/01_SideLit/README.md` and `02_BackLit_Frosted/README.md` to `docs/fabrication/`; `git rm -r Prototypes`.
- **Done when:** no `Prototypes/` dir; architecture doc no longer needs to explain it.

### P0-06 Delete the three stopgap Pico firmwares
- **Why:** Each opens with "standalone Pico light controller (stopgap)", one-day commits 2026-05-29/30, zero references anywhere, each duplicates the 15-line PIO driver from `TreeHouse_PicoLEDs`. Superseded 1:1 by `TreeHouse_Controllers/src/targets/{swannatopia,jess,julia,dormer}.h`.
- **Do:** `git rm -r Firmware/Club_Pico Firmware/HouseSwarming_Pico Firmware/Fungi_Pico` (283 LOC).
- **Done when:** gone; `Firmware/README.md` (P1-05) lists them as retired.

### P0-07 Untrack `.vscode` cache, add PlatformIO ignores
- **Why:** `Firmware/TreeHouse_Controllers/.vscode/c_cpp_properties.json` (538 lines, 483 contain another machine's home path) and `launch.json` are tracked despite being in that project's own `.gitignore`.
- **Do:** `git rm --cached` both; add `**/.pio/`, `**/.vscode/c_cpp_properties.json`, `**/.vscode/launch.json`, `**/.vscode/ipch` to root `.gitignore`. Also delete `.gitignore:17` `layout_calibrated.json` (file removed by ADR-0015) and fix the stale `touch_test_pygame.py` comment at `:18`.
- **Done when:** `git ls-files -i -c --exclude-standard` is empty.

### P0-08 Fix `_save_local({})`
- **Why:** `FC/app.py:551` in `_do_restart()` writes `{}` to `captcha-settings.local.json`. That file is the per-host override (`load_settings`, `app.py:82-84`); this is the only writer. Any override is wiped on the first `R` key or `/api/restart`. Corner-cal leftover from ADR-0012, never removed by ADR-0013.
- **Do:** delete `_save_local` and the call. Add a restart test (none exists) that asserts the file is untouched. Fix `docs/FundingCAPTCHA.md:93` ("not gitignored" — it is, `.gitignore:19`).
- **Done when:** restart leaves the local file byte-identical; test proves it.

### P0-09 Delete Keepaway — D5: delete
- **Why:** `FC/games/body_keepaway.py` (498 LOC), `keepaway-body-levels.json`, `keepaway-body-taunts.json`, `captcha-settings.json:44-49`. `app.py:349-351` hardcodes `("bodycaptcha",)`; `test_app_games.py:26-28` asserts Keepaway is not loaded. Unplugged in #142 (Sept), untouched since June. Git history is the retention mechanism.
- **Do:** `git rm` the module and two JSON files; remove the settings block; drop the two assertions in `test_app_games.py`; delete `docs/games/keepaway.md` (P0-04 covers it). Also remove `BLUE` import and `hud_font`/`top_bar_height` imports left in `games/`.
- **Done when:** `grep -ri keepaway` returns only ADR-0013's historical note.

### P0-10 Delete FundingCAPTCHA dead members
- **Why/what:** `ScreenSavers/waiting.py` (stub; `pipes_3d.py:382-402` draws the same overlay) + its `screensavers.json` entry; `games/grid.py:18-24` 7 colour aliases, `:26,90-91` `CELL_PAD`/`inner_rect`, `:67,93-115` `_flashes`/`flash`/`draw_flashes`, `:97-102` `draw_background`, `:117-120` `blit_cell`; `app.py:69-73` unused colours, `:284-285` empty section header; `app.py` `/ws` status channel + `broadcast()` (`:104,133-163,189-194`) — no client connects (Dashboard uses `/health` + `/logs`); `body_blobs.py:127-129` `BodyBlobs.active`; `captcha-settings.json:6` `detection.min_blob_pixels` (never consulted by `detect_foreground`); stale comments in `deploy/captcha.service:1,6-7`.
- **Done when:** ~150 LOC gone; `make test` unchanged.

### P0-11 Delete `FC/distribution/` — D2: delete
- **Why:** 297 LOC + READMEs. All three scripts from one commit (#94, 2026-05-23), never edited; the editor changed three times in Sept with no rebuild trail; `BodyCaptchaEditor.command` (#152) is the newer teammate path and the README itself tells Mac users to commit on a branch instead. `merge_levels.py` has no tests. `bodycaptcha_editor.py:16-19` `sys.frozen` branch exists only for this.
- **Done when:** directory and frozen branch gone; `docs/FundingCAPTCHA.md:128` updated.

### P0-12 Delete dead IIVision RGB camera
- **Why:** `IIVision/camera.py:38-53, 303-425` `OrbbecRGBCamera`/`RGBFrame` existed only for the ArUco calibrator deleted by ADR-0015. Zero importers. Needs `cv2`, which no requirements file lists. Also exported from `__init__.py:18,34-35`.
- **Do:** delete the classes, the `cv2` import, the section headers, the `__init__` exports; drop unused imports `camera.py:19,23,91`; drop `Blob3D.cam_half_extents_m/median_z_m/sample_count` (`blob_tracker.py:81-83,429-431`, computed never read), `Calibration.delete()` (`:138-141`), `CalibrationConfig` (`:47-49`), `TrackState`/`PreStabilizeFilter` exports.
- **Done when:** ~150 LOC gone; IIVision tests pass.

### P0-13 Delete core dead code
- **What:** `TH/looking_glass/deploy/` (service self-declared OBSOLETE by ADR-0018; its `install.sh` is the only one adding the user to `_seat` — see P1-06); `scripts/hooks/smoke_test.py` (no-op stub, wired nowhere); `FB/flower_beds.py:128-135` `ControllerConfig` (unused, hardcodes `192.168.1.50`); `FB/visualizer.py:377-382` `_get_loop`; `FB/main.py:222-223,274` `calibration_state` (constant); unused setters `TH/displays/effect.py:51-62`, `video.py:57-61`, `led.py:49-53`, `base.py:58-62`, `coordinator.py:412-413` `Coordinator.get`; `FB/requirements.txt` `aiofiles`; `TH/requirements.txt` `numpy`; all pyflakes unused imports (list in core §2).
- **Done when:** ~110 LOC gone; pyflakes clean on `IIVision ShowControl/FlowerBeds ShowControl/TreeHouse ShowControl/Dashboard ShowControl/OSCFabric`.

### P0-14 Retire TreeHouse Pico LED path — D1: ESP32s installed, retire
- **Why:** ADR-0020 promised removal once ESP32 hardware is installed. ADR-0021 made the ESP32s standalone. The Pi path cannot drive the documented hardware anyway: `coordinator.py:177` reads `pico`, settings has `pico_dioramas`/`pico_structure`; single `PicoDriver` at `main.py:149`; pin collisions (`dormer.pico_pin=0` vs `dioramas[0]`, `porch_lights=1` vs `dioramas[1]`); `LEDDisplay.update()` ignores GardenState (`led.py:60-63`).
- **Do:** delete `pico_driver.py`, `displays/led.py`, `displays/effect.py`, `displays/porch_lights.py`, `LEDControllable`/`ChannelFrame`/`Color` in `base.py`, LED branches of `coordinator.py` (`DioramaConfig`, `DormerConfig`, F&F/porch config, `build_displays` LED cases, `get_all_frames`, `set_display_pattern`, `reset_porch_lights`), `test_forge_and_flora.py`, Dashboard LED/forge/porch controls (`treehouse.html` ~60 lines, `visualizer.py` endpoints `:92-127`), `Firmware/TreeHouse_PicoLEDs/`, `pico_*` + `attic` + `garage_windows` settings blocks, `--no-pico` flag, `docs/TreeHouse.md:15-17,164-171,234`. Finish the `*Display` → `*Controllable` rename at the same time (4 files). Mark ADR-0010 Superseded.
- **Done when:** `TH/` has one lighting path and the glossary's avoid-list matches the class names. ~800 LOC.

### P0-15 Fix Dashboard→TreeHouse controls
- **Why:** `TH/visualizer.py:112` calls nonexistent `Coordinator.set_forge_mode` → 500. `Dashboard/treehouse.html:45-47` sends `full`/`dim`/`off`; `displays/base.py:10-13` is `active`/`dim`/`inactive`. `Dashboard/serve.py` `POST /api/mode` is called by no page.
- **Do:** change button values; delete `/control/forge-mode` + its button (the whole path is a no-op since `effect.py:79` overwrites mode every frame). Decide whether `serve.py /api/mode` stays (ties to P0-16). Add a FastAPI TestClient test for each `/control/*` route; there are none.
- **Done when:** every Dashboard button does what its label says or does not exist.

### P0-16 Remove the 5 unimplemented OSC addresses — D3: remove from schema
- **Why:** ADR-0007 lists 11 addresses. `/flowerbeds/mode`, `/captcha/mode`, `/pipes/mode`, `/captcha/restart`, `/captcha/game_started` have no sender or receiver (only `OSCFabric/test_client.py:107` sends `game_started`). Only TreeHouse runs an OSC server. Dashboard relays mode into nothing for 3 of 4 Elements. Documented as live in `docs/FlowerBeds.md:103`, `docs/FundingCAPTCHA.md:158`, `docs/Dashboard.md:15,28`, ADR-0007:159-162.
- **Do:** strike the five rows from ADR-0007 and the three docs; delete `serve.py /api/mode` and `send_event("game_started")` test.
- **Done when:** every address in the schema has a grep-able sender and receiver; the Dashboard has no relay endpoint nobody calls.

### P0-17 Fix AGENTS.md and Makefile
- **What:** `AGENTS.md:13` `Blob3D.world_pos_cm()` → `IIVision.transforms.orbbec_to_world()` (`world_pos_cm` is a *field* on `TrackedBlob`). `AGENTS.md:15` "firmware reads a generated `config.h`" → true only for `TreeHouse_Controllers/include/net_config.h`; either say so or close P1-04 first. `AGENTS.md:8` "Node tests (FundingCAPTCHA)" → none exist since 2026-05-11; drop `node --test` from `Makefile`, `.github/workflows/tests.yml` setup-node step, and `requirements`. Same fixes in `docs/agents/python-conventions.md:20,28`, `running-and-testing.md:6`, `firmware.md:9`, `configuration.md:113`.
- **Done when:** every sentence in AGENTS.md is grep-verifiable.

### P0-18 Fix TreeHouse `settings.json` unread keys — mostly subsumed by P0-14
- **What:** `pico_dioramas`/`pico_structure` (code reads `pico`), `garage_windows.forge_and_flora.arc_led_count`/`bloom_led_count` (code reads `led_count`, default 48 on 20-px strips), `flicker_intensity` (code reads `base_`/`max_flicker_intensity`), whole `attic` block (nothing reads `attic`), `club_screen.interval_seconds` (club_screen reads six other keys), `looking_glass.mirror_depth` (read, never sent). ~25 lines.
- **Do:** delete or rename each so every key has a reader; `club_screen.py` should also honour `--config` (it always loads `./settings.json`) and stop hardcoding 800×480.
- **Done when:** a script that diffs settings keys vs `raw.get(...)` calls reports zero orphans.

### P0-19 Delete 16 unreferenced LFS images
- **Why:** `FC/images/yeavl_may/` holds 24 files; `bodycaptcha-levels.json` references 8 of them plus `images/jess.jpg`. The 16 are LFS objects pulled on every Pi install (`deploy/install.sh:30`).
- **Done when:** every tracked image is referenced by a level file.

---

## Phase 1 — Make packages and directories self-describing

| ID | Task | Effort | Gate | Source |
|---|---|---|---|---|
| P1-01 | Root `pyproject.toml`; delete `sys.path` hacks and per-Element `requirements.txt` | S | — | core §5 |
| P1-02 | One `load_network_config` | S | — | core §3b |
| P1-03 | Fix PlayingThePipes docs; add `PlayingThePipes/README.md` | S | — | firmware §3a, §6 |
| P1-04 | Finish `firmware_config_gen.py` for FlowerBeds | S | — | firmware §1d |
| P1-05 | README stubs: `IIVision/`, `OSCFabric/`, `FC/games/`, `Firmware/`, `scripts/` + 3 live firmware dirs | S | — | docs §7, firmware §1f |
| P1-06 | Shared `scripts/lib/install-element.sh`; fix `_seat` gap | S | — | core §3g, §8 |
| P1-07 | Fold `ESP32S3_SignsOfLife` into `TreeHouse_Controllers` as an env | S | — | firmware §1c |
| P1-08 | Run `pio test -e native` in CI | S | — | firmware §1e |
| P1-09 | Move `TouchOSC/` beside `FB/diag.py` or delete | S | — | firmware §4 |
| P1-10 | `requirements-dev.txt`: add `av`, `Pillow`, `pyserial` so no test silently skips | S | — | fundingcaptcha §7 CI |

### P1-01 Root `pyproject.toml`
- **Why:** No `pyproject`/`setup.py`/`conftest.py`. `FB/main.py:32,53`, `FC/app.py:42-44`, `body_blobs.py:28`, `body_grid_tester.py:47-48` do `sys.path.insert`. Tests pass only because `python -m pytest` puts cwd on `sys.path`. Four `requirements.txt` are partial, inconsistent copies.
- **Do:** the `pyproject.toml` in core §5 "Minimal change" (packages `IIVision`, `OSCFabric`; extras `flowerbeds`, `treehouse`, `dashboard`, `fundingcaptcha`, `dev`; `[tool.pytest.ini_options] testpaths`, `pythonpath=["."]`). `deploy/install.sh` → `pip install -e "$REPO_ROOT[<element>]"`. Delete `pytest.ini`, `requirements*.txt`, the `sys.path` lines. CI installs `.[dev,flowerbeds,treehouse,dashboard,fundingcaptcha]`.
- **Done when:** `pytest` from any cwd passes; `python -c "import IIVision, OSCFabric"` works after `pip install -e .`.

### P1-02 One `load_network_config`
- **Why:** Four implementations: `OSCFabric/config.py:13-20`, `TH/coordinator.py:169-175` (derives path from `--config`, so a non-default settings path silently loses network.json), `Dashboard/serve.py:34-37`, `FB/layout_tool.py:50-52`; plus the try/except block copied 3× in `FB/main.py:124-128,301-305,358-362`.
- **Do:** everyone imports `OSCFabric.load_network_config`; add `load_network_config_or_empty(log)`. `Dashboard/index.html:55-60` hardcodes the four `http_port`s that `network.json` already holds — serve them from `/api/network` or template them.
- **Done when:** `grep -rn "network.json" --include=*.py` shows one path resolution.

### P1-03 PlayingThePipes docs and README
- **Why:** `docs/PlayingThePipes.md:11,43,93`, `docs/bootstrap.md:173,198` name `PlayingThePipes.maxpat`, which has never existed on `main` (only on unmerged branch `claude/max-music-system-stub-z2Qs0`). Show patch is `Lamplight2026/patchers/Lamplight2026.maxpat`. "Max/RNBO" in 4 docs; no `rnbo~` anywhere. Engine externals (`grainflow~`, `abl.device.*`) are undocumented. COM port table "TBD" since May; `encoderin.maxpat` takes `serial #1`/`#2` as patcher args.
- **Do:** replace every path; drop RNBO; list externals and the two serial args; add `ShowControl/PlayingThePipes/README.md` naming the show project, `EncoderTester.maxpat`, `health_server.py`.
- **Done when:** an operator following `bootstrap.md` opens a file that exists.

### P1-04 Finish `firmware_config_gen.py` for FlowerBeds
- **Why:** `Firmware/FlowerBeds_Follow_ServoController/*.ino:25-27` hardcodes MAC and `192.168.1.51`; `scripts/hooks/firmware_config_gen.py:20` is a TODO. AGENTS.md constraint #3 and three docs claim otherwise. `firmware.md:10` already warns about MAC/IP collision on the second board.
- **Do:** render `config.h` for `flowerbeds_controller_1/2` (~20 lines Python); `#include "config.h"` in the sketch; gitignore or commit-by-design like `net_config.h`. Note `network.json` `firmware.*.mac` is read by nothing today.
- **Done when:** the `.ino` has no literal IP or MAC.

### P1-05 README stubs
- **Why:** Only 2 of 9 firmware dirs and 0 of the Python packages have one. A model opening `IIVision/` has no map. Contents per stub are specified in docs §7 "Per-directory README stubs" (≤20 lines each).
- **Do:** `IIVision/README.md`, `ShowControl/OSCFabric/README.md`, `FC/games/README.md`, `Firmware/README.md` (table: dir → board → drives → live/retired), `scripts/README.md`, and 10-line READMEs for `FlowerBeds_Follow_ServoController`, `TreeHouse_BranchController`, `PlayingThePipes_EncoderPico` (board, libs, protocol, flash).
- **Done when:** every top-level and firmware directory has a README that says what it is in ≤20 lines.

### P1-06 Shared installer; fix `_seat`
- **Why:** `FB/deploy/install.sh:30-62`, `TH/deploy/install.sh:8-52`, `Dashboard/deploy/install.sh:26-56` share SCRIPT_DIR/REPO_ROOT, `SERVICE_USER`, `pip3 install --break-system-packages`, the `sed User=` into `/etc/systemd/system`, `daemon-reload/enable/restart`, the echo trailer. `treehouse.service:16` sets `LIBSEAT_BACKEND=seatd` (needs group `_seat`) but the live `TH/deploy/install.sh` never adds it; only the obsolete `looking_glass/deploy/install.sh:20` does. Hardcoded `/home/ii/CommunityGarden` in all four `.service` files and `deploy.sh:76,78`.
- **Do:** `scripts/lib/install-element.sh` with `install_element <Element> <service> [apt...]`; each `deploy/install.sh` ≈ 8 lines; template `WorkingDirectory=` from `REPO_ROOT`; add `usermod -aG _seat` to TreeHouse. Drop stale comments in `flowerbeds.service:6-7`, `treehouse.service:6-7,22`.
- **Done when:** a fresh Pi with a non-default clone path installs and starts TreeHouse.

### P1-07 Fold `ESP32S3_SignsOfLife` into `TreeHouse_Controllers`
- **Why:** Its `platformio.ini:16-29` duplicates `TreeHouse_Controllers/platformio.ini:20-32` verbatim; second `.vscode/` and `.gitignore`. The README's boot-loop triage section is genuinely useful.
- **Do:** `[env:signsoflife]` with `build_src_filter`; move triage README into a "Bring-up" section of the main README; delete the directory.

### P1-08 Firmware tests in CI
- **Why:** 51 Unity tests across 4 suites (`pio test -e native`) exist and pass but nothing runs them; CI is Node + Python only.
- **Do:** add a `pio test -e native` job to `tests.yml` (or a Makefile target and a line in `firmware.md` saying it is manual).

### P1-09 `TouchOSC/`
- **Why:** A top-level directory for one 4 KB binary (4 faders → `/cg/ff/rot`). `FB/diag.py` does the same job from Python. Referenced by `running-and-testing.md:69`, `architecture.md:19`.
- **Do:** move to `ShowControl/FlowerBeds/tools/FlowerBedTester.tosc` with a 5-line README, or delete and fix the two refs.

### P1-10 Dev requirements
- **Why:** `requirements-dev.txt` lacks `av` (so `test_playlist_app` video tests `importorskip` → silently skipped in CI), `Pillow`, `pyserial` (no test imports `TH/main.py` *yet*). Superseded by P1-01's `dev` extra if done together.

---

## Phase 2 — Split by concern

| ID | Task | Effort | Gate | Source |
|---|---|---|---|---|
| P2-01 | Extract `FC/settings.py`, `camera_feed.py`, `monitor.py` from `app.py`; tester and shader stage import them | M | — | fundingcaptcha §3a–e, §4 |
| P2-02 | Collapse `shader_app` into `playlist_app --setup`; one Setup list | S | — | fundingcaptcha §3j–k, §4 |
| P2-03 | `shader_test_rig.py` + public `Renderer.read_buffer()`; tests move into `shaders/<name>/` | M | — | fundingcaptcha §3l, §4 tests |
| P2-04 | Prune layout-probing and half-float shader tests to spec-level behaviour | M | — | fundingcaptcha §4 tests, §7 |
| P2-05 | Split `app.main()` into `Kiosk` with per-state ticks; first state-machine tests | L | — | fundingcaptcha §4, §7 |
| P2-06 | Split `bodycaptcha_editor.py` into model/widgets/views; shared `levels.py` with the game | L | — | fundingcaptcha §3i, §4 |
| P2-07 | `games/grid.py` → `grid.py` + `shell.py`; `blowup.py`; tests for `Grid` and `_LevelBag` | S | — | fundingcaptcha §4, §7 |
| P2-08 | `body_grid_tester.py`: fold into `app.py --tester` or rebuild on P2-01 modules | S | — | fundingcaptcha §4 |
| P2-09 | `ShowWeb.LiveServer`; FlowerBeds HTML string → static file | M | — | core §3a, §4 |
| P2-10 | `OSCFabric/gate.py` `SignalGate`; `FabricClient` and `LocationSender` wrap it | S | — | core §3d |
| P2-11 | `FB/controllers.py` + `calibrate_motors.py` + `state.py`; `main.py` → ~180 LOC | M | — | core §3c, §4 |
| P2-12 | `IIVision/blob_tracker.py` → `types/calibration/detector`; rename `BlobTracker`→`BlobDetector`; add detect/calibrate tests | M | — | core §4 |
| P2-13 | `TH/coordinator.py` → `config.py` + `garden_state.py` + `branches.py`; `BranchController` as a `Controllable` | M | D1 ✓ first | core §4 |
| P2-14 | `shadertoy.py` → package (`setup/body/keyboard/blobs_contract/renderer`) | S | — | fundingcaptcha §4 |
| P2-15 | Settings `DEFAULTS` + startup validation for `captcha-settings.json` | S | after P2-01 | fundingcaptcha §5 |

### P2-01 Extract shared FundingCAPTCHA infrastructure
- **Why:** `app.py:218-281` camera thread ≈ `body_grid_tester.py:190-253`; `app.py:104-213` monitoring server ≈ `tester:105-185`; `app.py:80-87` `load_settings` byte-identical to `tester:75-82`; camera factory ×3 (`app:486-494`, `tester:489-497`, `shader_app:197-202`); slab/ROI defaults ×7 with values that disagree with the committed file (code 800–2500 mm / 640×400; file 1000–4000 / 480×480); slab-mask fold ×4; colour tables ×4. `shader_app.py` imports private `_camera_thread` from `app`, dragging pygame display code along for a 7-line function.
- **Do:** `settings.py` (`DIR`, `load_settings`, `DEFAULT_SLAB`, `default_roi`, `slab_color`, `slab_mask`), `camera_feed.py` (`CameraFeed.start/restart/stop`, `.queue`, standback gate, `make_camera`), `monitor.py` (`MonitoringServer(port, commands)`), `test_input.py`, `plugins.py` (`load_games`, `load_screensavers`). Tester and shader stage import these. Make code defaults equal the file.
- **Done when:** `grep -n "from app import" FC/*.py` is empty; one definition of each default.

### P2-02 One shader entry point
- **Why:** `shader_app.Rotation` (`:86-144`) ⊂ `playlist_app.Playlist` (`:225-334`); `shader_app.main` (`:330-362`) ⊂ `playlist_app.main` (`:365-411`); `shaders/setups.json` and `playlist.json:setups` are two hand-synced lists. Only `shader_app --setup NAME` has no playlist equivalent. Tests duplicate too (`test_shadertoy.py:307-345` vs `test_playlist_app.py:128-203`).
- **Do:** add `--setup` to `playlist_app` (one-item playlist); delete `Rotation`, `shader_app.main`, `setups.json`; rename remainder `shader_stage.py` (library); split `video_player.py` out of `playlist_app.py`. Update `docs/FundingCAPTCHA.md:74`, `deploy/captcha.service` comment, `test_shadertoy.py:179`.
- **Done when:** one entry point, one Setup list.

### P2-03 Shared shader test rig
- **Why:** `ctx()` fixture ×5 (`test_shadertoy:157-171`, `test_endless_sunset:22-36`, `test_hunter_bird:27-41`, `test_watering_can:59-73`, `test_rainbow_poop:44-58`); `Rig` class ×4; mask builders (`rect/person/walking/standing/flickering/both`) ×4; GLSL-const readers ×3 with three different mechanisms incl. an `eval()` mini-interpreter (`test_watering_can:23-50`). All four read private `Renderer._buffers[name].read_tex`. `test_playlist_app.py:11` imports fixtures from another test module.
- **Do:** `FC/shaders/shader_test_rig.py` (or `conftest.py`): `ctx`, `Rig`, masks, `glsl_consts()`, ~200 LOC. Add `Renderer.read_buffer(name)` beside `read_body()`. Move `test_<setup>.py` into `shaders/<setup>/` so a deleted Setup takes its tests with it. Note the pattern in `shaders/README.md` "Hand it in".
- **Done when:** −350 LOC; no test touches `_buffers`.

### P2-04 Prune layout and half-float tests
- **Why:** 2,804 LOC to test ~3,000 LOC of GLSL. `test_owner_is_record_slot`, `test_run_extents_span_leg_to_shoulder`, `test_walker_leaves_no_hold_trail` (asserts a quantisation encoding), `test_slot_tracks_record_id`, `test_ages_keep_time_in_half_floats` pin texel storage, not visitor-visible behaviour. `test_watering_can:271-292` parametrises on "coarsest half-float spacing"; `:598,610` assert llvmpipe f16 stalls. `grown()/seconds_to()` (`:318-329`) re-derive the GLSL growth curve in Python. Each Setup test renders hundreds of frames; `BigRig` renders 480×480 ×40 ×3.
- **Do:** keep 10–15 spec-level tests per Setup (the claims from the deleted design docs); move input-contract tests (Buffer A, blobs texture) to one `test_shader_contracts.py` owned by `shadertoy.py`/`body_blobs.py`; replace re-derived curves with monotonicity/ordering asserts or recorded fixtures; add a `--durations` budget check in CI.
- **Done when:** suite is <1,500 LOC and CI GL time is bounded.

### P2-05 `Kiosk` class
- **Why:** `app.main()` is 350 lines (`:408-752`) holding the BG_CAL/SCREENSAVER/GAME machine in 15 loose locals and closures; the `R`-key and HTTP restart blocks are two slightly different copies (`:583-591` resets `sil_cache`, `:598-604` does not). Zero tests on the show path; P0-08's bug would have been caught by any restart test.
- **Do:** `kiosk.py` with `AppState`, `Kiosk` dataclass, `_tick_bg_cal/_tick_screensaver/_tick_game`, one `restart()`. `app.py` → argparse + wiring (~40 LOC). Add tests for transitions, standback/countdown gating (`:649-687`), attract dwell, OSC throttle, restart.
- **Done when:** `app.py` <100 LOC; state machine has tests.

### P2-06 Editor split; shared `levels.py`
- **Why:** `bodycaptcha_editor.py` is one 700-LOC class mixing model, widgets, three screens. Levels-path override is duplicated (`games/bodycaptcha.py:30-46` vs `editor:20-32`), `_img_load` duplicated (game version has an LFS-pointer check the editor lacks), `DEFAULT_LEVEL` exists three times with three different values. `Editor.__init__` opens a display, so `test_bodycaptcha_editor.py:22-33` opens one to test string logic. `set_levels_path` is module-global; two test files need autouse restore fixtures and `test_app_games.py:45-50` exists only to detect leakage.
- **Do:** `FC/levels.py` (`read_levels`, `write_levels`, `DEFAULT_LEVEL`, `Levels` object passed into the game, `load_image`); `editor/{levels_io,widgets,level_model,views}.py`; `bodycaptcha_editor.py` → run loop + argparse. `BodyCaptchaGame` takes `(WW, WH)` instead of reading `pygame.display.get_surface()` (`bodycaptcha.py:202`) so tests stop opening displays.
- **Done when:** no file >300 LOC; no test opens a display to test non-drawing logic; no autouse restore fixtures.

### P2-07 `grid.py` / `shell.py` / `blowup.py`
- **Why:** ADR-0019 suggested `games/shell.py`; implementer put the shell renderers in `grid.py`. `Grid` letterbox maths, `_fit_prompt_font`, `_wrap_to_width`, `draw_center_text` binary search are pure and untested. `_LevelBag` difficulty rule ("same or +1, fallback to all") is an ADR-0013 claim with no test. Timer-expiry → BLOWUP → DONE → `"loss"` path untested.
- **Done when:** `grid.py` ~60, `shell.py` ~130, `blowup.py` ~60; tests for `Grid`, `_LevelBag`, blow-up path.

### P2-08 `body_grid_tester.py`
- **Why:** 626 LOC, half of it P2-01's duplication; reads config keys `grid` and `activation_rule` that exist in no settings file; 3 commits since May; `docs/FundingCAPTCHA.md:249-254` shows an invocation that enters LIVE with no frames.
- **Do:** either `app.py --tester` (debug overlays, opt-in raw/delta payload on `CameraFeed`) or a ~300-LOC standalone on the shared modules. Delete or document the tester-only keys and flags (`--cols/--rows/--debug/--port 8081`, keys `D`/`C`).

### P2-09 `ShowWeb.LiveServer`
- **Why:** `WebSocketLogHandler`, `/ws`, `/logs`, `/health`, module globals, fan-out loop, uvicorn config are byte-for-byte duplicated between `FB/visualizer.py:312-404` and `TH/visualizer.py:32-184`; `/health` a third time in `Dashboard/serve.py:49-51`. 240 of `FB/visualizer.py`'s 434 lines are an HTML/JS string (`:66-305`); the layout tool next door already uses `StaticFiles`. Dashboard `flowerbeds.html` ≡ `fundingcaptcha.html` except a port; `appendLog/connectLogs` JS repeated ×3.
- **Do:** `ShowControl/ShowWeb/live.py` `LiveServer(logger_name, port, html, extra_routes)` with `start_in_thread()` and `async serve()`, `broadcast()`; `Dashboard/log-panel.js`; `FB/visualizer_static/index.html`. API in core §3a.
- **Done when:** both visualizers <60 LOC Python; no HTML in `.py`.

### P2-10 `SignalGate`
- **Why:** `OSCFabric/client.py:39-56` and `TH/location_sender.py:129-148` implement the same ADR-0007 change-epsilon + heartbeat rule differently (single vs N targets, `tick(dt)` vs wall clock, float-only vs float+string). `FabricClient.report()` of an unchanged value never refreshes `_elapsed`.
- **Do:** `OSCFabric/gate.py` `SignalGate(heartbeat_interval_s, change_epsilon, clock).due(key, value)/mark()`; both become thin wrappers.

### P2-11 FlowerBeds `main.py` split
- **Why:** `main.py` mixes config/network loading (×3 copies), camera factory, controller bus + diagnostics (`:74-115`, discovery duplicated at `:92-97` and `layout_tool.py:55-61`), calibration persistence, frame loop, visualizer state assembly, and two motor-calibration CLIs (`:292-411`, 120 LOC, no IIVision). `/cg/ff/rot` + yaw negation defined in both `flower_beds.py:164-167` and `layout_tool.py:71-75`; `_OSC_ADDRESS` in both `main.py:56` and `layout_tool.py:31`. Signal-handler boilerplate ×3 (`:198-206, 331-338, 388-395`).
- **Do:** `controllers.py` (`OSC_ROT_ADDRESS`, `Controller`, `controllers_from_network`, `ControllerBus.send/diagnose`), `calibrate_motors.py` (own entry point), `state.py` (visualizer `*State` TypedDicts move here so `flower_beds.py:21` stops importing the web layer); `config.py` for the dataclasses in `flower_beds.py:34-152`. API in core §3c.
- **Done when:** `main.py` ≈ 180 LOC; layout tool and main share one controller module.

### P2-12 `IIVision/blob_tracker.py` split
- **Why:** Three concerns in 434 LOC: dataclasses `:29-90`, calibration `:97-216`, detector `:223-434`. `BlobTracker` is a misnomer (per-frame detection; tracking is `BlobStabilizer`); `docs/FlowerBeds.md:11,36` already confuses them. No tests cover `Calibrator.build`, `BlobTracker.detect`, `_compute_3d_blobs`, `transforms.py`, `run_pipeline` — the production CV path.
- **Do:** `types.py`, `calibration.py`, `detector.py` (`BlobDetector`, alias `BlobTracker`); `camera.py` → `orbbec.py` + `mock.py` after P0-12. Add tests for calibrate and detect on synthetic frames.
- **Done when:** each file <220 LOC; CV path has tests.

### P2-13 `TH/coordinator.py` split — after P0-14
- **Why:** 9 config dataclasses `:33-125` + 110-line `load_config` `:132-275` + factory `:282-311` + `Coordinator` `:318-485` mixing Fabric intake/stale-sender policy, GardenState assembly, branch math, LED aggregation. `DioramaConfig`/`DormerConfig` mirror `LEDConfig` field-for-field. ADR-0006 wanted `BranchController(Controllable)`; it is a plain serial driver with the math in `Coordinator._update_branch_positions`.
- **Do:** `config.py` (dataclasses with `from_dict`, `load_config`), `garden_state.py` (`SignalIntake`: setters, `_expire_stale_senders`, `snapshot()`; `test_dead_sender.py` targets this and stops asserting private attrs), `branches.py` (`branch_positions()` pure function + `BranchController(Controllable)`), `coordinator.py` ~80 LOC.

### P2-14 `shadertoy.py` package
- **Why:** Coherent but 468 LOC; `body_blobs.py` imports the renderer module for 6 constants. Low urgency.
- **Do:** `shadertoy/{setup,body,keyboard,blobs_contract,renderer}.py` per fundingcaptcha §4.

### P2-15 Settings defaults and validation
- **Why:** Every `settings.get(key, default)` carries its own default; `BlobConfig.from_dict` (`body_blobs.py:49-51`) silently drops unknown keys so typos are invisible; `detection.max_depth_mm` is likely a no-op for the foreground path; `slab_styles` readers all hardcode `["0"]`.
- **Do:** `DEFAULTS` dict or dataclass in `settings.py`; warn on unknown keys at startup.

---

## Phase 3 — Docs: one job per file

| ID | Task | Effort | Gate | Source |
|---|---|---|---|---|
| P3-01 | `docs/repo-map.md` (≤50) replaces `architecture.md` | S | after P0 | docs §7 |
| P3-02 | `docs/osc-fabric.md` (≤50): the one address table; ADR-0007 keeps rationale | S | after P0-16 | docs §3 |
| P3-03 | Collapse `docs/agents/` to `conventions.md`, `firmware.md`, `git-workflow.md` | S | — | docs §7 mapping |
| P3-04 | Element docs: fix listed stale claims, cut to targets | M | after P0/P2 | docs §2 |
| P3-05 | `CONTEXT.md` → glossary only (≤130); add the 5 location names; resolve `Show Mode` and `Bloom` collisions | S | after P0-14 | docs §2 CONTEXT.md |
| P3-06 | ADRs: status line on all, truncate 0004/0009/0011, cut 0015 plan, fix 0010/0017/0018, renumber 0021→0023, 0022→0024, add `adr/README.md` | S | — | docs §4 |
| P3-07 | `showtime.md`/`bootstrap.md` fixes: step 2, `--no-locations`, ESP32 + WiFi provisioning, drop "serials in network.json" | S | — | docs §2 |
| P3-08 | `AGENTS.md` ≤40 lines, links to repo-map and element docs | S | after P3-01 | docs §7 |
| P3-09 | Delete `docs/audit/` once this backlog is in the tracker | S | last | — |

### P3-04 Element doc fixes (the specific false claims)
- **FlowerBeds.md:** `:11,36` BlobTracker→BlobStabilizer for EMA; `:103` `/flowerbeds/mode` (per D3); `:146` `calibration_state` is constant; absorb module table from `python-conventions.md` and the 6-line pipeline diagram from `architecture.md`.
- **TreeHouse.md:** `:14,194-205` four → five controllers (Garage 192.168.1.64); `:196` controllers ignore GardenState (ADR-0021); `:11,15-17,164-171,218,234` Pico content per D1; `:181,185` dioramas are generic `LEDDisplay`, no attic code exists; `:201-210` add `/lookingglass/*` on :9001.
- **FundingCAPTCHA.md:** `:11,162-170` monitoring page is JSON, not HTML; `:93` `.local.json` is gitignored; `:101` threshold default 0.25 in file; `:108,137` drop keepaway; `:146` pipes_3d is garden vines; `:152` 10 Hz not per-frame; `:158` `/captcha/mode` per D3; `:249-254` tester flags; `:74` verify or remove "not yet verified on Pi 5"; move maintenance mode (`:186-245`) to `showtime.md`; private content (`:273-398`) → ≤30 lines; absorb games table. Target ≤200 lines.
- **Dashboard.md:** `:15,28` relay reaches TreeHouse only; delete `network.json` copy `:52-64`; `:74` state the fact.
- **PlayingThePipes.md:** covered by P1-03.

### P3-05 CONTEXT.md specifics
- `:85,88` "Display (old name — being replaced)": either P0-14 renamed the classes or delete the note.
- `:58` four dioramas → five locations (Swannatopia, Julia, Jess, Dormer, Garage — none appear today).
- `:94` "4–6 Branches" → settings has 1 motor; `:97` "Bloom" collides with the F&F bloom strip and `bloom.glsl`; no aggregate Bloom exists in code.
- `:128` Signal Bag exists only in C++ firmware, inert since ADR-0021.
- `:47` Games list → BodyCaptcha only.
- `:41` "Show Mode (FundingCAPTCHA)" collides with TreeHouse `ShowMode` enum.
- `:134` FundingCAPTCHA now uses `BlobStabilizer` (ADR-0022).
- `:22-31` and `:91` GardenState fields listed twice; keep one, point at `displays/base.py`.
- `:111-120` OSC table → link to `docs/osc-fabric.md`.

---

## Side items already filed

- **#174** Delete 17 stale remote branches.

## Counting

| Phase | Items | Effort (person-days) | Lines removed |
|---|---|---|---|
| 0 | 19 | 3–4 | ~160,000 |
| 1 | 10 | 2–3 | ~300 net (adds READMEs, removes requirements) |
| 2 | 15 | 8–10 | ~1,500 + 350 test boilerplate, moves ~2,000 into smaller files |
| 3 | 9 | 2–3 | ~6,000 of docs |
