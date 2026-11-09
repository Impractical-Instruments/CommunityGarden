# Codebase audit — 2026-11-09

Five-minute read. Goal of the audit: make the repo parseable by humans and small-context models — each directory readable alone, no dead code, no doc that lies. Four auditors covered FundingCAPTCHA, the rest of ShowControl + IIVision, Firmware/Prototypes/PlayingThePipes, and docs. Every claim below has file:line evidence in [`detail/`](detail/). Actionable items with IDs are in [`backlog.md`](backlog.md).

Baseline at HEAD `56de83c`: 207 commits since 2026-01-24; `make test` = 303 pytest pass, 192 skip (no GL), `node --test` finds 0 tests.

## 1. The shape of the problem

| | Tracked lines | Of repo | Verdict |
|---|---|---|---|
| `ShowControl/PlayingThePipes/Pipes Prototype 3/` | 133,349 | 65% | Dead. Nothing live references it. 110 files, 6.8 MB, 112 MB LFS. |
| `ShowControl/PlayingThePipes/MakeNoiseDay/` | 16,557 | 8% | Vendored personal synth library; the show patch uses 2 of 26 files. |
| `docs/superpowers/` + `docs/PRD.md` + `docs/games/` + templates | ~5,300 | 2.6% | Planning transcripts and pre-festival snapshots. All features shipped. |
| `Prototypes/` | 1,942 | 1% | Zero symbols shared with production. |
| Three "stopgap" Pico firmwares + tracked `.vscode` cache | ~870 | 0.4% | Superseded 1:1 by ESP32 targets; 483 lines of another machine's home dir. |
| Dead/duplicated Python (both ShowControl audits, conservative) | ~2,200 | 1% | Unloaded game, dead camera class, 5 copies of a GL test rig, 4 loaders of `network.json`, 2 WebSocket servers. |
| **Removable with no design decision** | **~160,000** | **78%** | |

What remains after that is ~45k lines: ~13.6k production Python, ~6.5k test Python, 3.3k GLSL, 3.4k live firmware, ~12k lines of the one live Max project, ~3k docs.

## 2. Three live bugs and two broken contracts

1. **FundingCAPTCHA restart wipes per-host config.** `app.py:551` writes `{}` to `captcha-settings.local.json` on every `R` key or `/api/restart`. The file is documented as the per-host override and is read at boot; this is the only writer. Leftover from deleted corner-calibration.
2. **Two Dashboard→TreeHouse buttons 500 or no-op.** `TreeHouse/visualizer.py:112` calls a `Coordinator.set_forge_mode` that does not exist. `Dashboard/treehouse.html:45-47` sends `full`/`off`; the enum is `active`/`dim`/`inactive`.
3. **TreeHouse Pico config is unread.** `coordinator.py:177` reads key `pico`; `settings.json` has `pico_dioramas`/`pico_structure`. Driver falls back to `/dev/ttyACM0`; two pins collide. Masked because the ESP32 controllers now light the house standalone.
4. **AGENTS.md constraint #3 is violated by the repo's own firmware.** FlowerBeds `.ino:25-27` hardcodes MAC and `192.168.1.51`; `firmware_config_gen.py:20` has FlowerBeds as a TODO. Three docs say the generated `config.h` exists.
5. **5 of 11 OSC Fabric addresses were never implemented.** Only TreeHouse has an OSC listener. `/flowerbeds/mode`, `/captcha/mode`, `/pipes/mode`, `/captcha/restart`, `/captcha/game_started` are documented in four places and relayed by the Dashboard into nothing.

Also: AGENTS.md constraint #1 names `Blob3D.world_pos_cm()`, which does not exist (it is `transforms.orbbec_to_world()`); AGENTS.md says `make test` runs Node tests (none exist since May).

## 3. Why small models struggle here today

- **No packaging.** No `pyproject.toml`; Elements reach `IIVision`/`OSCFabric` via `sys.path.insert`. Tests pass only because of pytest's cwd behaviour. A reader cannot tell what any package depends on.
- **Three products in one folder.** `FundingCAPTCHA/` holds the kiosk, the shader player, and the level editor, sharing `app.py` as an accidental library (`shader_app.py` imports a private `_camera_thread` from it).
- **Big files holding whole state machines as locals.** `app.py` 756 (350-line `main()`), `bodycaptcha_editor.py` 847, `body_grid_tester.py` 626 (160 lines copied from `app.py`), `coordinator.py` 485, `main.py` 454, `visualizer.py` 434 (240 of which are an HTML string), `blob_tracker.py` 434.
- **Tests that reimplement the thing under test.** 2,804 lines of shader behaviour tests copy the GL rig five times, probe private buffer layouts, and re-derive GLSL curves in Python, including an `eval()`-based GLSL const reader. Good idea, unsustainable form.
- **Docs that contradict code and each other.** 70 doc files, 9,353 lines. The OSC table is in 8 places; `network.json` is pasted verbatim in 3, all stale. `docs/agents/domain.md` and `triage-labels.md` are unmodified third-party templates. Two ADRs are numbered 0021. The glossary forbids the class names the code uses (`*Display`) because a rename stalled in May.
- **Operators are sent to files that never existed.** `PlayingThePipes.maxpat` is named in three docs; the show patch is `Lamplight2026/patchers/Lamplight2026.maxpat`. "Max/RNBO" appears in four docs; no patch contains `rnbo~`.

## 4. The plan, in four phases

**Phase 0 — Delete (1–2 days, no decisions).** Tag and delete Pipes Prototype 3; collapse MakeNoiseDay into Lamplight2026; delete `docs/superpowers/`, `docs/PRD.md`, `docs/games/`, the two template docs; delete `Prototypes/` (move 2 fabrication READMEs); delete 3 stopgap Picos, dead IIVision RGB camera, unloaded Keepaway game, stub screensaver, `looking_glass/deploy/`, `smoke_test.py`; untrack `.vscode` cache; drop `node --test`. Fix the three bugs and the two AGENTS.md falsehoods in the same pass. Result: 78% fewer lines, every surviving directory is live.

**Phase 1 — Make packages real (1 day).** Root `pyproject.toml` with `IIVision` and `OSCFabric` installable and per-Element extras; delete `sys.path` hacks and the four `requirements.txt`; TreeHouse and Dashboard import `OSCFabric.load_network_config` instead of their own. Finish `firmware_config_gen.py` so constraint #3 is true. Per-directory README stubs (≤20 lines) for `IIVision/`, `OSCFabric/`, `games/`, `Firmware/`, `scripts/`, `PlayingThePipes/`.

**Phase 2 — Split by concern (4–6 days, mostly mechanical).** FundingCAPTCHA: extract `settings.py`/`camera_feed.py`/`monitor.py` from `app.py`; collapse `shader_app` into `playlist_app --setup`; shared `shader_test_rig.py` and public `Renderer.read_buffer()`, tests move into `shaders/<name>/`. Core: `ShowWeb.LiveServer` replaces two identical WebSocket servers; `blob_tracker.py` → `types/calibration/detector`; `FlowerBeds/main.py` → `controllers.py` + `calibrate_motors.py`; `coordinator.py` → `config/garden_state/branches`. Every file lands under ~300 LOC.

**Phase 3 — Docs to one job each (1–2 days, after code settles).** 70 files → ~30, 9.3k lines → ~3k. New `docs/repo-map.md` and `docs/osc-fabric.md` as the single homes for layout and addresses; `docs/agents/` shrinks to `conventions`, `firmware`, `git-workflow`; ADRs get a status line, truncated superseded bodies, a README index, and the 0021 collision renumbered. `CONTEXT.md` becomes glossary-only and gains the five location names it currently omits.

## 5. Decisions (made 2026-11-09)

| # | Decision | Outcome | Effect |
|---|---|---|---|
| D1 | ESP32-S3 controllers installed? | **Yes** | Execute ADR-0020's removal of the Pi Pico LED path (P0-14, P0-18, P2-13 ungated). |
| D2 | Windows PyInstaller editor build still used? | **No** | Delete `distribution/` (P0-11). |
| D3 | Five unimplemented OSC addresses | **Remove from schema** | Strike from ADR-0007 and docs; delete Dashboard `/api/mode` relay (P0-16). |
| D4 | 20 unreferenced Lamplight2026 media files | **Keep all** | P0-03 reduces to deleting the byte-identical Prototype 3 copies, which P0-01 already does. |
| D5 | Keep `body_keepaway.py`? | **Delete** | P0-09 ungated. |
| D6 | Where do Pipes samples live? | **Git LFS here** | No change. |

Nothing in Phase 0 is gated any more.

## 6. Where to drill down

- [`backlog.md`](backlog.md) — 40 tasks with IDs, effort, gates, files, done-when, and source section.
- [`detail/fundingcaptcha.md`](detail/fundingcaptcha.md) — 487 lines: inventory, dead code, 13 duplication sites, module splits, config key→reader table, test critique.
- [`detail/showcontrol-core.md`](detail/showcontrol-core.md) — 780 lines: IIVision/FlowerBeds/TreeHouse/Dashboard/OSCFabric/scripts, packaging plan, settings keys nothing reads, ADR-by-ADR drift.
- [`detail/firmware-prototypes-pipes.md`](detail/firmware-prototypes-pipes.md) — 253 lines: live/dead per firmware dir, Max patch reachability analysis, media sizes, LFS.
- [`detail/docs.md`](detail/docs.md) — 466 lines: every doc with verdict, every stale claim doc:line → code, redundancy map, target doc tree, README stub contents.

This directory is itself temporary: once the backlog is in the issue tracker, delete `docs/audit/`.
