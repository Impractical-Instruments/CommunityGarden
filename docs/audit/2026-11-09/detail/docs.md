# CommunityGarden documentation audit — 2026-11-09

Read-only audit of every tracked `.md` (66 files, 7,949 lines) plus the 4 `.html` mockups under `docs/superpowers/specs/` (1,404 lines). Six `.html` files under `ShowControl/Dashboard/` and `ShowControl/FlowerBeds/layout_tool/` are application UI, not docs, and are out of scope.

Repo history (full clone, 207 commits, first commit 2026-01-24). Code last touched: FundingCAPTCHA 2026-11-08, IIVision 2026-11-05, TreeHouse/Firmware/scripts/PlayingThePipes 2026-10-27, FlowerBeds/Dashboard/OSCFabric 2026-05-29.

Headline numbers:

| | files | lines |
|---|---|---|
| All docs audited | 70 | 9,353 |
| Recommend **delete** | 31 | 5,290 (57%) |
| Recommend **merge into another doc** | 12 | ~1,000 |
| Recommend **keep (edit in place)** | 27 | ~3,050 → target ≈ 2,000 |

---

## 1. Inventory

Audience: **op** = show operator / crew; **dev** = developer; **agent** = AI agent entry/guidance; **hist** = historical / planning artefact.

| File | LOC | Last commit | Audience | Purpose (one line) | Verdict |
|---|---|---|---|---|---|
| `AGENTS.md` | 32 | 2026-09-06 | agent | Entry point: test cmd, 6 constraints, links to docs/agents | keep, fix 3 claims |
| `CONTEXT.md` | 219 | 2026-05-29 | dev/agent | Domain glossary + OSC table + relationships | keep, cut ~40%, fix 9 stale terms |
| `README.md` | 25 | 2026-05-29 | op/dev | Landing page, element table, doc links | keep |
| `docs/bootstrap.md` | 314 | 2026-09-06 | op | One-time hardware provisioning per machine | keep, fix 4 claims |
| `docs/showtime.md` | 238 | 2026-05-29 | op | Daily ops, services, deploy, troubleshooting | keep (best doc in repo) |
| `docs/Dashboard.md` | 78 | 2026-05-29 | op/dev | Dashboard endpoints, service, network.json copy | keep, cut network.json copy, fix relay claim |
| `docs/FlowerBeds.md` | 131 | 2026-05-29 | op/dev | FlowerBeds architecture, settings, flags, OSC, troubleshooting | keep (canonical element doc) |
| `docs/TreeHouse.md` | 239 | 2026-09-06 | op/dev | TreeHouse architecture, flags, weston, renderer, locations | keep, fix 4→5 controllers |
| `docs/FundingCAPTCHA.md` | 398 | 2026-11-08 | op/dev | Everything FundingCAPTCHA incl. shader/playlist players, private content | keep, cut to ≤200 (move ops to showtime, shrink private-content) |
| `docs/PlayingThePipes.md` | 102 | 2026-05-29 | op | Health server, Max patch, COM ports, deploy | keep, fix maxpat name |
| `docs/PRD.md` | 214 | 2026-05-29 | hist | Pre-festival product requirements (May 2026) | delete (or move to docs/history/) |
| `docs/agents/architecture.md` | 111 | 2026-05-29 | agent | Repo tree (stale) + FlowerBeds-only pipeline | merge → rewrite as 40-line repo map |
| `docs/agents/configuration.md` | 113 | 2026-05-29 | agent | Stale settings.json + network.json copies | merge → element docs; delete copies |
| `docs/agents/domain.md` | 51 | 2026-05-29 | agent | Generic "how to use CONTEXT.md" template from mattpocock/skills | delete |
| `docs/agents/firmware.md` | 35 | 2026-10-27 | agent | Firmware index (4 of 9 dirs) | keep, fix hardcoded-IP claim, add missing dirs → 25 lines |
| `docs/agents/git-workflow.md` | 12 | 2026-09-06 | agent | Branch/PR rules, private-content hook | keep |
| `docs/agents/issue-tracker.md` | 22 | 2026-05-29 | agent | `gh issue` cheat sheet | merge into git-workflow.md |
| `docs/agents/python-conventions.md` | 44 | 2026-05-29 | agent | FlowerBeds module table, coordinate/rotation/logging conventions | keep rotation+logging; move module table to FlowerBeds.md |
| `docs/agents/running-and-testing.md` | 69 | 2026-05-29 | agent | FlowerBeds-only run/test (incomplete flag table) | merge into AGENTS.md (3 lines) + FlowerBeds.md |
| `docs/agents/triage-labels.md` | 15 | 2026-05-29 | agent | Label mapping template, still says "Edit the right-hand column" | delete (or fold 5 lines into git-workflow) |
| `docs/adr/0001` OSC as fabric | 7 | 2026-05-29 | dev | Why OSC/UDP | keep, add status, amend |
| `docs/adr/0002` dwell cluster-local | 14 | 2026-05-29 | dev | Dwell semantics in FlowerCluster | keep |
| `docs/adr/0003` games self-terminate | 9 | 2026-05-29 | dev | Every Game must lose on inactivity | keep |
| `docs/adr/0004` depth touch detection | 37 | 2026-05-29 | hist | Superseded by 0013 (marked) | keep header, truncate body |
| `docs/adr/0005` branch USB serial | 23 | 2026-05-29 | dev | Branch controller JSON-lines over USB | keep |
| `docs/adr/0006` Controllable hierarchy | 33 | 2026-05-29 | dev | Controllable / LEDControllable split | keep, note per-room subclasses never built |
| `docs/adr/0007` OSC fabric schema | 92 | 2026-05-29 | dev | Address table, fire semantics, network.json | keep; mark 5 unimplemented addresses; delete network.json copy |
| `docs/adr/0008` GardenState mapping | 91 | 2026-05-29 | dev | Per-display personality | keep; mark LookingGlass/`overload`/`GardenStateResponse` as not built |
| `docs/adr/0009` ArUco layout | 38 | 2026-05-29 | hist | Superseded by 0015 (marked) | delete-safe (0015 restates context) |
| `docs/adr/0010` Pico LED arch | 69 | 2026-05-29 | hist | Two Picos, udev symlinks | **status wrong** (Accepted → Superseded by 0020) |
| `docs/adr/0011` screen calibration | 36 | 2026-05-29 | hist | Superseded by 0013 (marked) | keep header, truncate body |
| `docs/adr/0012` unified pygame app | 53 | 2026-05-29 | dev | Single app.py process | keep; strike games/pairs.json paragraph |
| `docs/adr/0013` silhouette interaction | 98 | 2026-05-29 | dev | Body Grid, Depth Slabs, Arc state machine | keep (core), add Status |
| `docs/adr/0014` Pipes encoder Picos | 53 | 2026-05-29 | dev | 2 Picos → USB serial → Max | keep |
| `docs/adr/0015` GUI layout tool | 215 | 2026-05-29 | dev | Layout tool design + 110-line done implementation plan | keep, cut plan → ~90 lines |
| `docs/adr/0016` test-input mode | 54 | 2026-05-29 | dev | Mouse-paint depth frames | keep, add Status |
| `docs/adr/0017` club rave screen | 65 | 2026-05-29 | dev | Club diorama 800×480 pygame screen | keep, fix paths |
| `docs/adr/0018` weston dual display | 95 | 2026-05-29 | dev | Single weston, pygame+moderngl | keep, fix 3 claims |
| `docs/adr/0019` game UI shell | 71 | 2026-05-29 | dev | Top bar + maximal grid | keep, add Status |
| `docs/adr/0020` ESP32-S3 controllers | 113 | 2026-10-27 | dev | One ESP32 per location, Garden State over OSC | keep |
| `docs/adr/0021-fundingcaptcha-shader-player` | 30 | 2026-11-05 | dev | Shadertoy Setups on the Pi | keep, **renumber → 0023** |
| `docs/adr/0021-treehouse-controllers-standalone…` | 99 | 2026-10-27 | dev | Controllers ignore Garden State; Garage welder | keep (owns 0021) |
| `docs/adr/0022` blob records | 40 | 2026-11-05 | dev | `blobs` channel source | keep, **renumber → 0024**, fix link |
| `docs/games/bodycaptcha.md` | 81 | 2026-05-29 | dev | BodyCaptcha design | merge into FundingCAPTCHA.md games section (or games/bodycaptcha.py docstring) |
| `docs/games/bodygrid.md` | 46 | 2026-05-29 | dev | Body Grid input layer | merge → body_grid.py docstring; delete |
| `docs/games/keepaway.md` | 120 | 2026-05-29 | dev | Keepaway design (module not loaded) | merge → body_keepaway.py docstring; delete |
| `docs/games/rhythm.md` | 25 | 2026-05-29 | hist | Deleted game, "port TODO" since May | delete (→ GitHub issue if still wanted) |
| `docs/games/upsidedown.md` | 23 | 2026-05-29 | hist | Deleted game, "port TODO" since May | delete (→ GitHub issue) |
| `docs/superpowers/plans/2026-09-06-private-content-sets.md` | 949 | 2026-09-06 | hist | Step-by-step implementation plan with full code listings | delete |
| `docs/superpowers/plans/2026-10-30-endless-sunset.md` | 500 | 2026-10-30 | hist | Implementation plan | delete |
| `docs/superpowers/plans/2026-11-04-hunter-bird.md` | 470 | 2026-11-05 | hist | Implementation plan | delete |
| `docs/superpowers/plans/2026-11-06-watering-can.md` | 424 | 2026-11-06 | hist | Implementation plan | delete |
| `docs/superpowers/specs/2026-09-06-private-content-sets-design.md` | 150 | 2026-09-06 | hist | Design spec, "Approved, pending implementation" (shipped) | delete |
| `docs/superpowers/specs/2026-10-30-endless-sunset-design.md` | 103 | 2026-10-30 | hist | Setup design | delete (salvage 1 line) |
| `docs/superpowers/specs/2026-10-30-endless-sunset-mockup.html` | 149 | 2026-10-30 | hist | Canvas mockup | delete |
| `docs/superpowers/specs/2026-11-04-hunter-bird-design.md` | 118 | 2026-11-06 | hist | Setup design | delete (salvage 1 line) |
| `docs/superpowers/specs/2026-11-04-hunter-bird-mockup.html` | 502 | 2026-11-05 | hist | Mockup (linked from ADR-0022) | delete; fix link |
| `docs/superpowers/specs/2026-11-05-hunter-bird-two-eyes-mockup.html` | 657 | 2026-11-06 | hist | Mockup | delete |
| `docs/superpowers/specs/2026-11-06-watering-can-design.md` | 132 | 2026-11-06 | hist | Setup design incl. "Revisions after first build" | delete (salvage 2 lines) |
| `docs/superpowers/specs/2026-11-06-watering-can-mockup.html` | 96 | 2026-11-06 | hist | Mockup | delete |
| `docs/superpowers/specs/2026-11-08-rainbow-poop-design.md` | 78 | 2026-11-08 | hist | Setup design | delete (salvage 1 line) |
| `Firmware/ESP32S3_SignsOfLife/README.md` | 101 | 2026-09-06 | dev/op | Bring-up/diagnostic firmware for ESP32-S3 boards | keep |
| `Firmware/TreeHouse_Controllers/README.md` | 174 | 2026-10-27 | dev/op | Build, flash, self-test, retune the 5 location controllers | keep (canonical) |
| `Prototypes/GlowPanels/README.md` | 58 | 2026-05-29 | hist | Mycelium glow-panel prototype comparison | delete with `Prototypes/GlowPanels/` (or keep if the physical prototyping continues) |
| `Prototypes/GlowPanels/01_SideLit/README.md` | 137 | 2026-05-29 | hist | Build notes, prototype 1 | delete |
| `Prototypes/GlowPanels/02_BackLit_Frosted/README.md` | 169 | 2026-05-29 | hist | Build notes, prototype 2 | delete |
| `ShowControl/FundingCAPTCHA/distribution/README.md` | 85 | 2026-09-30 | dev | Build/ship Windows level editor, merge contributions | keep |
| `ShowControl/FundingCAPTCHA/shaders/README.md` | 91 | 2026-11-05 | dev (shader authors) | Shadertoy prototyping rules + hand-in | keep (canonical) |
| `ShowControl/FundingCAPTCHA/videos/README.md` | 8 | 2026-11-08 | op | Where video files go | keep |
| `ShowControl/PlayingThePipes/MakeNoiseDay/other/README.md` | 10 | 2026-09-25 | — | Vendored third-party README ("WineAndWiresMax", Twitch/YouTube links) | delete |

---

## 2. Accuracy audit — stale or false claims

Every claim below was checked against the working tree. Format: `doc:line` → what the code actually does.

### AGENTS.md (the agent entry point — these matter most)

- **L8** "`make test` runs Node tests (FundingCAPTCHA)" → There are no JS tests. The only `.test.js` ever (`ShowControl/FundingCAPTCHA/touch-input.test.js`) was deleted 2026-05-11 ("delete browser stack"). The only JS file in the repo is `ShowControl/FlowerBeds/layout_tool/layout.js`. `Makefile` still runs `node --test`, which finds nothing.
- **L13** "`IIVision.Blob3D.world_pos_cm()` converts between them" → `Blob3D` (IIVision/blob_tracker.py:76) has no such method. The conversion is `IIVision.transforms.orbbec_to_world()` (transforms.py:62). `world_pos_cm` is a *field* on `TrackedBlob`.
- **L15** constraint 3: "firmware reads a generated `config.h`" → `Firmware/FlowerBeds_Follow_ServoController/FlowerBeds_Follow_ServoController.ino:25-26` hardcodes `byte mac[] = {0xDE,0xAD,0xBE,0xEF,0x15,0x01}` and `IPAddress ip(192,168,1,51)` and includes no `config.h`. `scripts/hooks/firmware_config_gen.py:20` says `TODO: generate Firmware/FlowerBeds_Follow_ServoController/config.h too.` Only `Firmware/TreeHouse_Controllers/include/net_config.h` is generated. The repo's own constraint is violated by the repo's own firmware, and three docs (AGENTS, configuration.md:113, firmware.md:9, ADR-0007:212) assert otherwise.

### docs/agents/architecture.md

- **L5-26 repo tree** is missing: `Firmware/{Club_Pico, Fungi_Pico, HouseSwarming_Pico, PlayingThePipes_EncoderPico, ESP32S3_SignsOfLife, TreeHouse_Controllers}` (6 of 9 firmware dirs), `ShowControl/PlayingThePipes/`, `Prototypes/`, `scripts/{deploy.sh, bootstrap-deploy.sh, install-services.sh, install-git-hooks.sh, git-hooks/}`, `requirements-dev.txt`, `docs/{games,superpowers}`. 
- **L25** "pytest.ini testpaths = ShowControl IIVision" → actual: `ShowControl IIVision scripts`.
- **L33-40 IIVision table** omits `silhouette_warp.py` (`reproject_silhouette`), `OrbbecRGBCamera`/`RGBFrame`, `Calibrator`, `DetectionConfig`, `filter_positions_near_points`, `PreStabilizeFilter`, `update_tracks()` (ADR-0022).
- **Whole file**: titled "Architecture & Pipeline" but L47-111 is FlowerBeds only. TreeHouse, FundingCAPTCHA and Pipes architecture live in their `docs/<Element>.md`. An agent reading this gets a 1-of-4 picture.

### docs/agents/configuration.md

- **L7-70** FlowerBeds `settings.json` example diverges from the real file: real has `activity_max_blobs`, `_comment` keys, camera `mirror: true`, `pos_cm [-484,0,290]`, `rotation pitch -30 / yaw 90`; the documented `"serial"` key (L64, L75) is **not a field** of `CameraConfig` (flower_beds.py:139-152) and is silently dropped. `yaw_limit_deg` — the one per-cluster key operators actually tune — is absent.
- **L96-110** `network.json` copy is missing `lan`, `change_epsilon`, and the five `treehouse_{swannatopia,julia,jess,dormer,garage}` entries (5 of 8 firmware entries).
- **L113** "Firmware reads addresses from a generated `config.h`" → false for FlowerBeds (see AGENTS L15).
- Title says "per Element" but covers only FlowerBeds; nothing on `TreeHouse/settings.json` (12 top-level keys) or `captcha-settings.json`.

### docs/agents/running-and-testing.md

- **L6** "Node tests (FundingCAPTCHA)" → none exist.
- **L37-47** flag table omits `--recalibrate`, `--calibrate-yaw-sweep`, `--sweep-period-s` (main.py:421-437). `docs/FlowerBeds.md:80-91` has the complete, correct table.
- FlowerBeds-only; TreeHouse/FundingCAPTCHA dev commands are in `showtime.md:154-171`.

### docs/agents/python-conventions.md

- **L20** "`Blob3D.world_pos_cm()` converts camera → world" → `orbbec_to_world()` (transforms.py:62). Mapping on L21-23 is correct.
- **L29** rotation order ✓ matches `rotator_to_matrix` (`"yxz"`: roll, pitch, −yaw). The yaw negation is not mentioned; worth one line.
- **L44** "never `print`" → `layout_tool.py`, `visualizer.py`, `bodycaptcha_editor.py`, `distribution/*.py` all use `print`. Either the rule is wrong or scoped to the frame loop.
- Logger name `"flower_beds"` ✓; other Elements use `treehouse`, `captcha`, `osc_fabric`, `shader_app`, `pipes-health` — doc doesn't say.

### docs/agents/firmware.md

- **L9** FlowerBeds "IP and MAC come from a generated `config.h`" → hardcoded (see above).
- Missing entirely: `Club_Pico`, `Fungi_Pico`, `HouseSwarming_Pico` (standalone "stopgap" MicroPython controllers — their docstrings say so; undocumented anywhere), `PlayingThePipes_EncoderPico` (only mentioned in PlayingThePipes.md), `ESP32S3_SignsOfLife` (has its own README). 5 of 9 firmware dirs undocumented here.
- L18-31 ESP32 content is accurate but duplicates `Firmware/TreeHouse_Controllers/README.md`.

### docs/agents/domain.md

- **Entire file** is an unmodified template from mattpocock/skills: references `CONTEXT-MAP.md`, `src/<context>/docs/adr/`, `/grill-with-docs`, example ADRs "0001-event-sourced-orders", "0002-postgres-for-write-model". None exist here. Zero repo-specific content. The title "Domain glossary & vocabulary" in AGENTS.md is misleading — the glossary is `CONTEXT.md`.

### docs/agents/triage-labels.md

- L5 header "Label in mattpocock/skills"; L15 "Edit the right-hand column to match whatever vocabulary you actually use" — template instruction left in. Label existence on GitHub not verifiable from this session (GraphQL blocked).

### docs/agents/issue-tracker.md

- L14 "see the global instructions for the `gh pr create` example" → dangling reference; the example is in git-workflow.md.

### CONTEXT.md

- **L85** Controllable: "_Avoid_: 'Display' (the old name — being replaced)" and **L88** "_Avoid_: 'LEDDisplay' (the old name — being replaced)" → rename is half-done and has been for 5+ months. Base classes are `Controllable`/`LEDControllable` (displays/base.py:51,73) but **every concrete class is still `*Display`**: `LEDDisplay` (led.py:22), `ForgeAndFloraDisplay` (effect.py:22), `PorchLightsDisplay` (porch_lights.py:26), `LookingGlassDisplay` (video.py:20); the package is `displays/`. The glossary forbids the word the code uses.
- **L58** "Four dioramas exist: House Swarming, Club, Mycelium, Forge & Flora" → `settings.json` has 3 `dioramas` + Forge & Flora under `garage_windows`. More importantly the house is now organised as five **locations** — Swannatopia, Julia, Jess, Dormer, Garage (ADR-0020/0021, network.json, settings.json `locations.controllers`) — and **none of those five names appears in CONTEXT.md**.
- **L94** Branch "4–6 motorised branches" → `settings.json branch_controller.motors` has 1 motor. **L97** "Bloom: 0.0–1.0 value… aggregate extension state of all Branches" → no such concept in code; `coordinator.py:453-466` computes a per-motor weighted `signal` → degrees between `min_pos`/`max_pos`, with `recoil_pos` on blowup. In code "bloom" means the Forge & Flora bloom strip (`bloom_pin`) and a Looking Glass shader (`bloom.glsl`). The glossary's "Bloom" actively collides with two real things.
- **L128** Signal Bag: "pattern used inside individual Controllable implementations" → exists only in C++ firmware (`Firmware/TreeHouse_Controllers/lib/Patterns/Patterns.h`); no Python Controllable has one; and ADR-0021 made the weights inert.
- **L47** Game: "Examples: BodyCaptcha, UpsideDown, Rhythm, Keepaway. `app.py` loads all Games" → `app.py:349-351 _load_games` loads `("bodycaptcha",)` only. UpsideDown/Rhythm code was deleted (ADR-0013, 2026-05); Keepaway exists but is not loaded (#142).
- **L41** "Show Mode (FundingCAPTCHA)" = automated game rotation → collides with TreeHouse `ShowMode` enum (`active`/`dim`/`inactive`, base.py:10) which is a `GardenState` field (L26, L91 of the same file). Same term, two meanings, in the file whose job is to prevent that.
- **L134** IIVision "used by FundingCAPTCHA (background subtraction + denoising only — blob detection not used)" → since ADR-0022 (2026-11-05) `body_blobs.py` runs IIVision `BlobStabilizer.update_tracks()` for the shader player.
- **L22-31 and L91**: GardenState fields listed twice in the same file.
- **L111-120** OSC table ✓ matches `osc_server.py` but omits `/lookingglass/{scene,time,intensity}` (osc_server.py:8, TreeHouse.md:118-122) and `/cg/ff/{rot,ping,pong,hb}`.
- L75 Attic TV "8 LEDs" ✓; L64 Mycelium "224 LEDs" ✓; L43 pipes screensaver ✓; L111-120 ✓.

### docs/showtime.md

- **L51-57** "Daily startup" list numbered 1, 3, 4, 5, 6 — step 2 missing.
- **L160** TreeHouse no-hardware command omits `--no-locations` (TreeHouse.md:46), so it will UDP-spam 192.168.1.60-64.
- Everything else checked (ports, service names, deploy.sh usage, journalctl, state machine) ✓. This is the most accurate doc in the repo.

### docs/bootstrap.md

- **L13** treehouse hardware "2× Pi Pico, 1× branch controller, 2× HDMI" → omits the 5× ESP32-S3 WiFi location controllers (192.168.1.60-64), which are now the primary lighting path. Nowhere in bootstrap/showtime is the WiFi network they join provisioned (the show LAN is described as wired, no DHCP; `secrets.h` holds credentials for an AP that is not documented).
- **L127** "Record the serials in `ShowControl/network.json` under `firmware`" → `network.json` has no `serial` field; schema is `{ip, mac, osc_port}`.
- **L173, L198** `PlayingThePipes.maxpat` → does not exist. Actual: `Lamplight2026/Lamplight2026.maxproj`, `Pipes Prototype 3/Pipes Prototype 3.maxproj`, `MakeNoiseDay/MakeNoiseDay.maxproj`, `EncoderTester.maxpat`.
- L73 FlowerBeds install.sh has no udev rule ✓ (confirmed). L94-97 TreeHouse apt list ✓.

### docs/Dashboard.md

- **L15, L28** `POST /api/mode` "relays show mode to a specific Element over OSC" → only TreeHouse has an OSC server (`osc_server.py`). FlowerBeds `main.py`, FundingCAPTCHA `app.py` and Pipes have **no OSC listener**. The relay to 3 of 4 elements is a no-op. L78 hedges ("Element doesn't listen") where it should state the fact.
- **L52-64** `network.json` copy stale (missing `mac`, `lan`, `change_epsilon`, `treehouse_*`).
- L5 `cg-dashboard`, port 9000 ✓ (serve.py:96, install.sh:31).

### docs/FlowerBeds.md

- **L103** `/flowerbeds/mode | in (Fabric) | relayed by Dashboard` → nothing in FlowerBeds listens for OSC.
- **L11, L36** "cross-frame stabilisation (`BlobTracker` with EMA smoothing)" → that is `BlobStabilizer`; `BlobTracker` is per-frame detection.
- Flags table L80-91 ✓ exact match to main.py:416-437. Layout tool flags ✓ (layout_tool.py:219-224). `yaw_limit_deg` default 60 ✓. `/cg/ff/{ping,pong}` ✓.

### docs/TreeHouse.md

- **L14** "4× ESP32-S3 location controllers — Swannatopia, Julia, Jess, Dormer" and **L194-205** table of 4 → there are **5** (Garage, 192.168.1.64; `settings.json locations.controllers` lists 5; `platformio.ini` has `env:garage`; ADR-0021).
- **L196** describes controllers following Garden State; omits that they currently ignore it (ADR-0021, `kFollowGardenState=false`). firmware.md:23 says so; TreeHouse.md doesn't.
- Not mentioned: `looking_glass/deploy/looking_glass.service` + `install.sh` still in tree though ADR-0018:1108 says "obsolete and must not be installed".
- Flags L40-51 ✓ (main.py:32-43). weston.ini L73-91 ✓ byte-identical. GardenState L182-188 ✓.

### docs/FundingCAPTCHA.md

- **L158** `/captcha/mode | s (in)` → app.py has no OSC listener; only outbound `FabricClient` (app.py:478).
- **L101** `cell_activation_threshold` "default 0.30" → `captcha-settings.json` ships 0.25 (code default is 0.30).
- **L61** links to four `docs/superpowers/specs/*-design.md` — breaks if specs are deleted. The tunable names it lists are already at the top of each `common.glsl`.
- L5, L42-46, L65-71, L87, L96-108, L135-138, L146 all ✓ against app.py / shader_app.py / playlist_app.py / captcha-settings.json / games/ / ScreenSavers/.
- Structural: L186-245 (maintenance mode) and L273-398 (private content, 125 lines) are operations prose; the private-content section documents 3 commands and 2 env vars.

### docs/PlayingThePipes.md

- **L11, L43, L93** `PlayingThePipes.maxpat` → does not exist (see bootstrap). The directory's actual content (Lamplight2026, Pipes Prototype 3, MakeNoiseDay — last touched 2026-10-27) is not mentioned.
- **L57-60** COM-port table still "TBD".
- L13 "does not yet join the OSC Fabric" ✓ consistent with code. L17 health_server 55 lines ✓, port 8767 ✓. `Firmware/PlayingThePipes_EncoderPico/` ✓ exists.

### docs/games/*.md

- **bodygrid.md:100** "`BodyGridActivator` class (in `games/grid.py`)" → it is in `body_grid.py:47`.
- **bodycaptcha.md:4** "Status: In implementation (2026-05-13)" → shipped; **L30** "hold progress bar" → replaced by hold-ring (ADR-0019). Config block L71-78 lacks `hold_decay_rate` (real file has it).
- **keepaway.md:135** "Implemented as … body_keepaway.py" → true but not loaded by app.py (:349-351); doc doesn't say. "designed to be winnable" (L141) sits oddly against CONTEXT "no overall victory condition".
- **rhythm.md, upsidedown.md**: describe code deleted 2026-05; "Port TODO" open 6 months with no issue linked.

### ADRs — factual errors (status review is in §4)

- **0001:8** "addresses configured statically in each Element's `settings.json`" → superseded by `network.json` (ADR-0007).
- **0007:154,159-162** `/captcha/game_started`, `/flowerbeds/mode`, `/captcha/mode`, `/captcha/restart` (OSC), `/pipes/mode` → **never implemented**; no OSC listener exists outside TreeHouse. **0007:155** intensity "`level / total_levels`" → now weighted difficulty+time (CONTEXT L72). **0007:212** `config.h` → false for FlowerBeds. **0007:195-210** network.json copy stale.
- **0008:264-282** LookingGlass mood-mirror scene selection and `overload` scene → **not built**: `video.py:36 SCENES` is still the four scenes; `update()` (video.py:67-75) just sends the configured scene and a mean intensity. **0008:284-294** `GardenStateResponse` config block → does not exist; `LEDDisplay.update()` (led.py:60-100) selects pattern from static config. Branches ✓ (coordinator.py:453-466 incl. recoil), ForgeAndFlora ✓ (effect.py:78), Porch ✓.
- **0006:133** "Each room becomes its own class (`HouseSwarmingDisplay`, `ClubDisplay`, `AtticDisplay`)" → never built; all use generic `LEDDisplay`.
- **0010:412** "Udev rules are generated by `scripts/install-services.sh` using serial numbers recorded in `network.json`" → neither exists (install-services.sh has no udev; network.json has no serials; bootstrap.md:99-129 says do it by hand).
- **0012:507-511** games "UpsideDown, Rhythm, Keepaway", `pairs.json`, `rhythm-images.json`, `keepaway-images.json` → none of these files exist.
- **0017:976, 978, 1016-1017** paths `treehouse/club_screen.py` → `ShowControl/TreeHouse/club_screen.py`.
- **0018:1057** "`weston.ini` (in `looking_glass/deploy/`)" → `ShowControl/TreeHouse/deploy/weston.ini`. **0018:1062** `shell=kiosk-shell.so` → actual file uses `desktop-shell.so` with a `[shell]` block. **0018:1108** "`looking_glass.service` is obsolete and must not be installed" → still tracked at `looking_glass/deploy/`.
- **0020:1217-1219, 1276-1281** "four locations", "four environments" → amended to five by 0021 (header says so ✓; body not updated).

### In-tree READMEs

- `Firmware/TreeHouse_Controllers/README.md` — all checked claims ✓ (5 envs + 5 selftest + native in platformio.ini:50-104; IPs match network.json; `src/targets/{dormer,garage,jess,julia,swannatopia}.h`).
- `Firmware/ESP32S3_SignsOfLife/README.md` ✓.
- `shaders/README.md` ✓ (setups.json lists 5; `blob_debug/`, `blob_painter.glsl`, `body_painter.glsl` exist).
- `distribution/README.md` ✓ (build.py, package.py, merge_levels.py, TEAMMATE_README.txt, BodyCaptchaEditor.command exist).
- `Prototypes/GlowPanels/README.md` tree ✓ (`firmware/panel_gradient.py` exists).
- `PlayingThePipes/MakeNoiseDay/other/README.md` — third-party content, nothing to check.

---

## 3. Redundancy map

| Fact | Stated in | Canonical home | Delete from |
|---|---|---|---|
| OSC Fabric address table | CONTEXT.md:111-120; ADR-0007:151-163; TreeHouse.md:213-223; firmware.md:25; ADR-0020:1246-1253; FlowerBeds.md:97-103; FundingCAPTCHA.md:154-158; `osc_server.py` docstring | **`ShowControl/TreeHouse/osc_server.py` docstring** (it's the receiver) + one table in `docs/osc-fabric.md` (new, ≤40 lines, replaces the schema half of ADR-0007) | CONTEXT.md (link instead), firmware.md, ADR-0020 body; element docs keep only *their* outbound rows |
| `network.json` contents verbatim | configuration.md:96-110; ADR-0007:195-210; Dashboard.md:52-64 — all three stale | **The file itself** (it already carries a `_comment`) | all three |
| World coordinate system | AGENTS.md:10; python-conventions.md:14-25; configuration.md:76-78; ADR-0015:736; `transforms.py` docstring | **AGENTS.md one line** + `IIVision/transforms.py` docstring | configuration.md; trim python-conventions to rotation convention |
| FlowerBeds CLI flags | running-and-testing.md:37-47 (incomplete); FlowerBeds.md:80-91 (complete); showtime.md:163 | **FlowerBeds.md** | running-and-testing.md |
| Layout tool usage | architecture.md:60-79; configuration.md:80-90; running-and-testing.md:49-61; FlowerBeds.md:42-74; ADR-0015 | **FlowerBeds.md** | architecture, configuration, running-and-testing |
| FlowerBeds pipeline narrative | architecture.md:47-107; FlowerBeds.md:9-15; PRD §3.1; CONTEXT.md FlowerBeds domain | **FlowerBeds.md** (+ `flower_beds.py` docstring already explains Attraction) | architecture.md (keep a 6-line pipeline diagram at most) |
| GardenState fields | CONTEXT.md:22-31 **and** :91 (same file twice); TreeHouse.md:182-188; ADR-0008; `displays/base.py:33` | **`displays/base.py` dataclass**; CONTEXT.md one entry | CONTEXT.md second copy; TreeHouse.md → "see base.py" |
| Glossary | CONTEXT.md vs docs/agents/domain.md | **CONTEXT.md** | domain.md (it isn't a glossary) |
| No-hardware dev commands | AGENTS.md:17; running-and-testing.md:19-23; showtime.md:154-171; each element doc | **element docs**; AGENTS.md keeps one FlowerBeds line | running-and-testing.md |
| Depth Slab / Body Grid config shape | CONTEXT.md:57-66; ADR-0013:556-566; games/bodygrid.md:116-126; FundingCAPTCHA.md:99-101 | **FundingCAPTCHA.md settings section** | bodygrid.md; CONTEXT.md keeps the definition, drops the JSON |
| Hosts / IPs / ports / service names | showtime.md:11-33; bootstrap.md:11-18; each element doc header; Dashboard.md:5 | **showtime.md machine map** | bootstrap.md table (link); element docs keep one header line |
| Private content sets | FundingCAPTCHA.md:273-398; git-workflow.md:3; AGENTS.md:21; spec+plan (1,099 lines); `.gitignore` comment; pre-commit header | **AGENTS.md rule** + FundingCAPTCHA.md ≤30 lines | spec, plan; shrink FundingCAPTCHA section |
| Pico A/B channel assignment | TreeHouse.md:16-17, 168-172; bootstrap.md:103-107; ADR-0010:382-384; PRD §3.2 | **`TreeHouse/settings.json`**; TreeHouse.md one table (hardware is being retired) | bootstrap.md, PRD |
| Captcha maintenance / console access | FundingCAPTCHA.md:186-245; showtime.md:203-210 | **showtime.md** | FundingCAPTCHA.md |
| ESP32 controller facts (5 envs, standalone, `kFollowGardenState`) | firmware.md:18-31; TreeHouse.md:194-207; `Firmware/TreeHouse_Controllers/README.md`; ADR-0020/21 | **`Firmware/TreeHouse_Controllers/README.md`** | firmware.md → 3 lines + link; TreeHouse.md → table + link |
| Test command | AGENTS.md:8; running-and-testing.md:6; Makefile | **Makefile** + AGENTS.md one line | running-and-testing.md |

---

## 4. ADR review

Status check done against the code. "No Status" = file has no `**Status:**` line.

| ADR | In force? | Status field | Recommendation |
|---|---|---|---|
| 0001 OSC as fabric | Yes, but L8 (addresses in `settings.json`) superseded by 0007 | none | **keep**; add `Status: Accepted; addressing amended by ADR-0007` |
| 0002 Dwell cluster-local | Yes (`flower_beds.py:42-61`) | none | **keep**; add status |
| 0003 Games self-terminate | Yes | none | **keep**; add status |
| 0004 Depth touch detection | Superseded (marked) | ✓ | **keep header, truncate body** to the superseded notice + 2 lines (37 → ~6) |
| 0005 Branch USB serial | Yes (`branch_controller.py` JSON lines) | ✓ | **keep** |
| 0006 Controllable hierarchy | Yes, but per-room subclasses (L133) never built | ✓ | **keep**; add note "per-room subclasses not built; generic `LEDDisplay` + config used instead" |
| 0007 OSC schema | **Partially** — 5 of 11 addresses never implemented; intensity semantics changed; network.json copy stale; `config.h` false | says Accepted | **keep, amend**: mark unimplemented rows, delete JSON copy, fix L212; or split: schema → `docs/osc-fabric.md`, keep ADR as rationale only |
| 0008 GardenState mapping | **Partially** — Branches ✓, F&F ✓, Porch ✓; LookingGlass mood-mirror + `overload` ✗; `GardenStateResponse` ✗. Also whole Pi-side LED path now superseded by 0020 and reactivity disabled by 0021 | says Accepted | **keep, mark** "Partially implemented; LED sections superseded by ADR-0020/0021" |
| 0009 ArUco layout | Superseded (marked) | ✓ | **delete-safe** — 0015 restates the context fully; else truncate like 0004 |
| 0010 Pico LED architecture | **Superseded by 0020** (0020 says so; 0010 doesn't). L412 udev-generation never built | **wrong: says Accepted** | **fix status → Superseded by ADR-0020**; truncate |
| 0011 Screen calibration | Superseded (marked) | ✓ | **keep header, truncate body** |
| 0012 Unified pygame app | Yes | none | **keep**; add status; strike L507-511 (UpsideDown/Rhythm/pairs.json never existed in this form) |
| 0013 Silhouette interaction | Yes — core design | none | **keep**; add `Status: Accepted; Supersedes 0004, 0011`; note L624 (Keepaway ported but unloaded; UpsideDown/Rhythm not ported) |
| 0014 Pipes encoder Picos | Yes (firmware exists; Max side unverified) | ✓ | **keep** |
| 0015 Layout tool | Yes | ✓ | **keep, cut** L822-888 implementation plan (done) → ~90 lines |
| 0016 `--test-input` | Yes (app.py:413-416) | none | **keep**; add status |
| 0017 Club screen | Yes | ✓ | **keep**; fix paths |
| 0018 weston dual display | Yes | ✓ | **keep**; fix weston.ini path, `desktop-shell.so`, and remove or acknowledge `looking_glass/deploy/looking_glass.service` |
| 0019 Game UI shell | Yes | none | **keep**; add status |
| 0020 ESP32 location controllers | Yes, amended | ✓ | **keep**; update "four" → "five" in body (header already says so) |
| **0021** TreeHouse standalone + Garage | Yes | ✓ | **keep**, owns number 0021 (committed 2026-10-27, first) |
| **0021** FundingCAPTCHA shader player | Yes, amended by 0022 | none | **renumber → 0023** (committed 2026-11-05, second). Update links in: `0022` header, `docs/FundingCAPTCHA.md:32`, `shaders/README.md` (none), `ADR-0022:1444` |
| 0022 Blob records | Yes | ✓ | **renumber → 0024** (so it follows what it amends); fix `superpowers/...mockup.html` link at L1448 → delete the link or replace with `shaders/hunter_bird/` |

**Numbering collision**: two files named `0021-*`. Both are current. Rename shader-player → `0023-fundingcaptcha-shader-player.md` and blob-records → `0024-shader-player-blob-records.md`; three link edits. Add a one-line `docs/adr/README.md` index so the next collision is visible.

**ADRs with no Status line** (10): 0001, 0002, 0003, 0012, 0013, 0016, 0019, 0021-shader, plus 0004/0011 use a blockquote instead of the field. Standardise on `**Status:**` as the first line under the title.

---

## 5. Superpowers specs & plans

All five features are shipped and tested:

| Feature | Shipped code | Tests | Spec | Plan | Mockups |
|---|---|---|---|---|---|
| Private content sets | `app.py --levels`, `arc.py`, `deploy/install.sh` sync, `scripts/git-hooks/pre-commit`, `.gitignore` | `test_bodycaptcha_levels.py`, `test_app_games.py`, `test_bodycaptcha_editor.py`, `scripts/test_git_hooks.py` | 150 ("Approved, pending implementation" — wrong, shipped 2026-09-06) | 949 | — |
| Endless sunset | `shaders/endless_sunset/{setup.json,common.glsl,image.glsl,…}`; in `setups.json`, `playlist.json` | `test_endless_sunset.py` | 103 | 500 | 149 |
| Hunter bird | `shaders/hunter_bird/`; `body_blobs.py`; `BlobStabilizer.update_tracks()`; ADR-0022 | `test_hunter_bird.py`, `test_body_blobs.py` | 118 | 470 | 502 + 657 |
| Watering can | `shaders/watering_can/` | `test_watering_can.py` | 132 | 424 | 96 |
| Rainbow poop | `shaders/rainbow_poop/` | `test_rainbow_poop.py` | 78 | — | — |

**Recommendation: delete all 13 files (4,328 lines, 46% of all doc lines).** The plans are superpowers-workflow transcripts with full code listings that now diverge from the shipped code. The specs' "decided" sections are restated in the shipped `common.glsl` headers and tests. Two inbound links must be fixed: `docs/FundingCAPTCHA.md:61` (four spec links) and `docs/adr/0022…:1448` (mockup link).

Worth salvaging (one line each, into the named destination):

- **private-content-sets-design.md §"Failure behaviour"** (L119-135) — the fallback contract (bad `--levels` → single built-in level, never refuse to start; mid-run bad reload keeps old levels) → already in `FundingCAPTCHA.md:316-327`; nothing to salvage.
- **endless-sunset-design.md §"Anti-goals"** (L25-30) — what the Setup must *not* do (e.g. no outline/fill of the body, no text) → one line in `shaders/endless_sunset/common.glsl` header.
- **hunter-bird-design.md §"Behaviour"** — the eye locks one person at a time, strikes once per person → one line in `shaders/hunter_bird/common.glsl` header (the blob-records *contract* is already ADR-0022).
- **watering-can-design.md §"Revisions after the first build"** (L127-132) and **§"Testing (decided)"** (L100-118) — the sideways-step-rewinds rule and the testing harness pattern (`ctx` fixture copied from `test_shadertoy.py`) → one line in `common.glsl` header; the fixture pattern deserves one sentence in `shaders/README.md` §"Hand it in" ("add a `test_<setup>.py` modelled on `test_watering_can.py`").
- **rainbow-poop-design.md §"Revisions after the first build"** (L71-78) → one line in its `common.glsl` header.
- **Nothing** from the four plans or the three HTML mockups.

If the team wants a place for future design-before-build artefacts, that place is a GitHub issue or PR description (git-workflow.md already says PRs carry the summary), not a tracked directory.

---

## 6. docs/PRD.md

**What it is**: a pre-festival Product Requirements Document, "Version 1.0", for the Connect Beyond Festival debut 29–31 May 2026. Created 2026-04-29, last substantively edited 2026-05-22/23, 214 lines.

**Is it current**: No. Every §3 "Status" line is a May-2026 snapshot ("Interaction pivot complete (2026-05-12)", "Physical structure under construction"). Concrete stale claims: §3.2 LED hardware = two Picos (superseded by ESP32-S3, ADR-0020); §3.3 "Pi 5 has no analog audio" in Open Q6 vs §3.3 body "Windows mini PC"; §3.4 lists `pairs.json`, `rhythm-images.json`, `keepaway-images.json` (don't exist) and says "/captcha/intensity … sent every 100ms" (sent on-change + heartbeat); §5 "static IPs hardcoded in `settings.json`" (contradicts `network.json`, ADR-0007); §6 Monitoring Dashboard described as TBD (built); Open Questions 7 and 8 still "TBD" six months after the festival. The festival it was written for is five months in the past; the installation has since toured (Carolina tweaks #141, Lamplight 2026 #155).

**Who reads it**: nobody operationally. The thematic intent (§1) and spatial layout (§2) are the only parts with lasting value and they are duplicated in `CONTEXT.md` (Elements section) and `README.md`.

**Recommendation**: delete. If the team wants the thematic-intent table and the layout diagram kept, move those ~30 lines into `README.md` (it already has the element table) and delete the rest. Do not keep a "living document" that hasn't lived since May.

---

## 7. Proposed target structure

Principle: one file per *job*; operators read `docs/`, developers read `docs/<Element>.md` + module docstrings, agents read `AGENTS.md` and follow links. Facts live where the code is.

```
CommunityGarden/
├── README.md                      (25)   what this is, element table, links to docs/ — keep as is
├── AGENTS.md                      (≤40)  agent entry: test cmd, constraints, repo map link, doc index
├── CONTEXT.md                     (≤130) glossary ONLY: terms + avoid-lists; no OSC table, no GardenState fields, no JSON
├── docs/
│   ├── showtime.md                (≤240) daily ops, machine map, services, deploy, troubleshooting (+captcha maintenance mode)
│   ├── bootstrap.md               (≤300) one-time provisioning (+ESP32 WiFi/AP, remove serials-in-network.json)
│   ├── repo-map.md                (≤50)  NEW: accurate directory tree with one line per dir — replaces architecture.md
│   ├── osc-fabric.md              (≤50)  NEW: the one address table (implemented vs planned), fire semantics, network.json schema — schema half of ADR-0007
│   ├── FlowerBeds.md              (≤150) element doc (+ module table from python-conventions)
│   ├── TreeHouse.md               (≤220) element doc (5 locations; link Firmware README)
│   ├── FundingCAPTCHA.md          (≤200) element doc (ops prose → showtime; private content ≤30 lines; games table absorbs games/*.md)
│   ├── PlayingThePipes.md         (≤90)  element doc (real Max project names)
│   ├── Dashboard.md               (≤50)  endpoints + "relay only reaches TreeHouse"
│   ├── agents/
│   │   ├── conventions.md         (≤40)  coordinate + rotation + logging + print rule (from python-conventions)
│   │   ├── firmware.md            (≤30)  index of all 9 Firmware/ dirs, one line each + links
│   │   └── git-workflow.md        (≤25)  branches, PRs, gh issue cheat-sheet, labels (absorbs issue-tracker, triage-labels)
│   └── adr/
│       ├── README.md              (≤30)  NEW: numbered index with status column
│       └── 0001…0024              (~900 total after truncating 0004/0009/0011, cutting 0015 plan, renumbering)
├── IIVision/README.md             (≤25)  NEW stub
├── ShowControl/OSCFabric/README.md(≤15)  NEW stub
├── ShowControl/TreeHouse/displays/… (docstrings; no README needed)
├── ShowControl/FundingCAPTCHA/
│   ├── shaders/README.md          (91)   keep
│   ├── distribution/README.md     (85)   keep
│   ├── videos/README.md           (8)    keep
│   └── games/README.md            (≤20)  NEW stub (replaces docs/games/)
├── Firmware/
│   ├── README.md                  (≤20)  NEW stub: which dir is live, which is stopgap, which is superseded
│   ├── TreeHouse_Controllers/README.md (174) keep
│   └── ESP32S3_SignsOfLife/README.md   (101) keep
└── scripts/README.md              (≤15)  NEW stub
```

Target: ~30 files, ~3,000 lines (from 70 files / 9,353).

### Mapping old → new

| Old | Action | New |
|---|---|---|
| `AGENTS.md` | keep, fix L8/L13/L15, relink | `AGENTS.md` |
| `CONTEXT.md` | keep, cut OSC table, GardenState copy, Signal Bag, Bloom, Branch count, Game list; add Location/Swannatopia/Julia/Jess/Dormer/Garage/Setup/Body/Playlist; resolve Display rename (either rename classes or drop the avoid-note); resolve Show Mode collision | `CONTEXT.md` |
| `README.md` | keep | `README.md` |
| `docs/showtime.md` | keep; fix numbering, add `--no-locations`; absorb FundingCAPTCHA maintenance mode | `docs/showtime.md` |
| `docs/bootstrap.md` | keep; fix maxpat, serials, add ESP32 controllers + WiFi | `docs/bootstrap.md` |
| `docs/agents/architecture.md` | **merge**: tree → `repo-map.md`; FlowerBeds pipeline → `FlowerBeds.md` (6-line diagram) | delete |
| `docs/agents/configuration.md` | **merge**: settings prose → `FlowerBeds.md` (it's already there); delete both JSON copies | delete |
| `docs/agents/running-and-testing.md` | **merge**: test cmd → AGENTS.md; flags → FlowerBeds.md (already complete there) | delete |
| `docs/agents/python-conventions.md` | **merge**: module table → FlowerBeds.md; rest → `agents/conventions.md` | rename |
| `docs/agents/domain.md` | **delete** (template) | — |
| `docs/agents/triage-labels.md` | **merge** 5 lines → git-workflow.md | delete |
| `docs/agents/issue-tracker.md` | **merge** → git-workflow.md | delete |
| `docs/agents/firmware.md` | keep, rewrite as index of 9 dirs | `docs/agents/firmware.md` |
| `docs/agents/git-workflow.md` | keep, absorb two files | `docs/agents/git-workflow.md` |
| `docs/Dashboard.md` | keep, cut JSON copy, state relay limitation | `docs/Dashboard.md` |
| `docs/FlowerBeds.md` | keep, fix BlobTracker/Stabilizer, drop `/flowerbeds/mode` row | `docs/FlowerBeds.md` |
| `docs/TreeHouse.md` | keep, 4→5, note standalone, link firmware README | `docs/TreeHouse.md` |
| `docs/FundingCAPTCHA.md` | keep, cut to ≤200: maintenance → showtime, private content ≤30, drop spec links, absorb games table | `docs/FundingCAPTCHA.md` |
| `docs/PlayingThePipes.md` | keep, real project names | `docs/PlayingThePipes.md` |
| `docs/PRD.md` | **delete** (optionally 30 lines → README) | — |
| `docs/games/bodycaptcha.md` | **merge** → `games/bodycaptcha.py` module docstring + FundingCAPTCHA.md games table | delete |
| `docs/games/bodygrid.md` | **merge** → `body_grid.py` docstring (already substantial) | delete |
| `docs/games/keepaway.md` | **merge** → `games/body_keepaway.py` docstring | delete |
| `docs/games/rhythm.md`, `upsidedown.md` | **delete**; open one GitHub issue "port UpsideDown/Rhythm to silhouette" if still wanted | — |
| `docs/superpowers/**` (13 files) | **delete**; 5 one-liners → `common.glsl` headers; fix 2 inbound links | — |
| `docs/adr/0007` schema half | **split** → `docs/osc-fabric.md`; ADR keeps rationale | both |
| `docs/adr/0021-fundingcaptcha-shader-player.md` | **renumber** | `0023-…` |
| `docs/adr/0022-shader-player-blob-records.md` | **renumber** | `0024-…` |
| `docs/adr/0004, 0009, 0011` | truncate to header + superseded note (or delete 0009) | same |
| `docs/adr/0010` | status → Superseded by 0020; truncate | same |
| `docs/adr/0015` | cut implementation plan | same |
| other ADRs | add Status, fix listed paths | same |
| `Firmware/TreeHouse_Controllers/README.md`, `ESP32S3_SignsOfLife/README.md` | keep | same |
| `Prototypes/GlowPanels/*.md` (3) | **delete** with the directory, or move the comparison table (README.md L12-24) into a GitHub issue; the Mycelium panel shipped | — |
| `ShowControl/FundingCAPTCHA/{shaders,distribution,videos}/README.md` | keep | same |
| `ShowControl/PlayingThePipes/MakeNoiseDay/other/README.md` | **delete** (third-party) | — |

### Per-directory README stubs (new)

A model that opens only this directory should get orientation in ≤20 lines.

**`IIVision/README.md`**
- One sentence: shared depth-camera CV library; public API is `IIVision/__init__.py` (import from the package, not submodules).
- Coordinate systems: camera X-right/Y-down/Z-forward metres → world X-right/Y-forward/Z-up cm via `orbbec_to_world()`.
- Module map: `camera.py` (Orbbec/Mock), `blob_tracker.py` (per-frame detection + calibration), `blob_stabilizer.py` (cross-frame IDs, `update()` vs `update_tracks()`), `pipeline.py` (wiring), `silhouette_warp.py` (FundingCAPTCHA reprojection), `transforms.py`.
- Consumers: FlowerBeds uses the full pipeline; FundingCAPTCHA uses calibration + subtraction + warp, and `BlobStabilizer` via `body_blobs.py`.
- Tests: `test_*.py` here; run with `python -m pytest IIVision`.

**`ShowControl/OSCFabric/README.md`**
- `FabricClient(element, network)`: `report(signal, value)` on-change + heartbeat; `send_event(addr)` immediate; `tick(dt)`.
- `load_network_config()` resolves `ShowControl/network.json`; schema is documented in `docs/osc-fabric.md`.
- Only TreeHouse *receives*; this package is the *sender* side.

**`ShowControl/FundingCAPTCHA/games/README.md`**
- Game interface (`create(settings) -> Game`, `update/draw/reset`, returns `(intensity, event)`).
- `bodycaptcha.py` is the only module loaded (`app.py:_load_games`); `body_keepaway.py` is retained but unloaded.
- `grid.py` = shared overlay/shell (ADR-0019). Input layer is `../body_grid.py`.
- Level data lives beside `app.py` (`bodycaptcha-levels.json`, `taunts.json`).
- Every Game must self-terminate (ADR-0003).

**`Firmware/README.md`**
- Table of the 9 dirs with status: **live** (`FlowerBeds_Follow_ServoController`, `TreeHouse_Controllers`, `TreeHouse_BranchController`, `PlayingThePipes_EncoderPico`), **diagnostic** (`ESP32S3_SignsOfLife`), **stopgap standalone** (`Club_Pico`, `Fungi_Pico`, `HouseSwarming_Pico` — no host, flash as `main.py`), **superseded** (`TreeHouse_PicoLEDs`, by ADR-0020).
- Which read generated config: only `TreeHouse_Controllers/include/net_config.h`; FlowerBeds `.ino` hardcodes IP/MAC (open item vs AGENTS constraint 3).
- Regenerate config: `python3 scripts/hooks/firmware_config_gen.py`.
- Cross-layer contract: `/cg/ff/rot` ↔ `ShowControl/FlowerBeds/main.py`.

**`scripts/README.md`**
- `deploy.sh <host> <Element>` — LAN push + install (venue); `bootstrap-deploy.sh` — one-time per Pi; `install-services.sh` — on-Pi installer wrapper.
- `install-git-hooks.sh` + `git-hooks/pre-commit` — private-content guard.
- `hooks/firmware_config_gen.py` — network.json → firmware headers; `hooks/smoke_test.py` — what it checks (one line).
- `test_git_hooks.py` runs under `make test`.

**`ShowControl/TreeHouse/README.md`** (optional; `docs/TreeHouse.md` covers it) — only if the team wants a pointer: "see `docs/TreeHouse.md`; `displays/base.py` defines `Controllable`/`GardenState`; `osc_server.py` docstring is the inbound OSC contract."

### Things the cleanup should also fix in code/config (not docs), because the docs can't be made true otherwise

1. `Makefile`: drop `node --test` (no JS tests since 2026-05-11) or add one; AGENTS.md L8 follows.
2. Either finish the `*Display` → `*Controllable` rename or delete the avoid-notes in CONTEXT.md.
3. Either generate `config.h` for the FlowerBeds `.ino` (the TODO in `firmware_config_gen.py:20`) or amend constraint 3 to say "TreeHouse controllers only, FlowerBeds pending".
4. Remove `ShowControl/TreeHouse/looking_glass/deploy/` (ADR-0018 says it must not be installed).
5. `docs/adr/` renumber (two 0021s).
