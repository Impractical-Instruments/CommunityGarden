# Audit: Firmware/, Prototypes/, ShowControl/PlayingThePipes/, TouchOSC/

Read-only audit of `the repo root` at HEAD `56de83c` (2026-11-08). Full history: 207 commits, 2026-01-24 → 2026-11-08. All paths below are relative to the repo root unless absolute.

Headline numbers (git-tracked, `du -k` blocks):

| Area | Files | Lines | Tracked KB | LFS objects behind pointers |
|---|---|---|---|---|
| Whole repo | 1 pack, 989 objects | — | 10,644 KB | 82 files, 230 MB declared |
| `ShowControl/PlayingThePipes/` | 181 | 163,521 | 8,000 KB (75% of repo) | 57 files, 226 MB (98% of LFS) |
| ↳ `Pipes Prototype 3/` | 110 | 133,349 | 6,832 KB (64% of repo) | 24 files, 112 MB |
| ↳ `MakeNoiseDay/` | 26 | 16,557 | 576 KB | 0 |
| ↳ `Lamplight2026/` | 42 | 11,804 | 660 KB | 33 files, 114 MB |
| `Firmware/` (9 dirs) | 46 | 5,117 (3,357 of which TreeHouse_Controllers code; 582 of which tracked `.vscode` junk) | 328 KB | 0 |
| `Prototypes/` (3 dirs) | 10 | 1,942 | 96 KB | 0 |
| `TouchOSC/` | 1 | (binary) | 4 KB | 0 |

---

## 1. Firmware inventory

Per-directory facts. "Refs" = anything outside the directory itself that names it (grep across repo, excluding `.git` and `__pycache__`).

| Dir | MCU / toolchain | Drives | Code LOC | Commits (first → last) | Refs outside dir | README | Status |
|---|---|---|---|---|---|---|---|
| `FlowerBeds_Follow_ServoController/` | OpenRB-150 (SAMD21), Arduino `.ino`; libs Dynamixel2Arduino, Ethernet, OSCMessage | Dynamixel servos via Ethernet+OSC `/cg/ff/rot`, `/cg/ff/ping|pong|hb` | 207 | 4 (2026-02-05 → 2026-05-25) | `AGENTS.md`, `docs/agents/firmware.md`, `docs/agents/architecture.md:16`, `ShowControl/FlowerBeds/diag.py:4`, `scripts/hooks/firmware_config_gen.py:19` | **no** | **LIVE** |
| `TreeHouse_BranchController/` | OpenRB-150 (SAMD21), Arduino `.ino`; libs Dynamixel2Arduino, ArduinoJson | Branch Dynamixels via USB JSON-lines (ADR-0005) | 132 | 1 (2026-05-03) | `docs/agents/firmware.md:17`, `architecture.md:17`; counterpart `ShowControl/TreeHouse/branch_controller.py` | **no** | **LIVE** |
| `PlayingThePipes_EncoderPico/` | RP2040 Pico, MicroPython | 6 quadrature encoders → `/enc BOARD ENC DELTA` over USB CDC (ADR-0014) | 52 | 1 (2026-05-22) | `docs/PlayingThePipes.md:18`; consumed by `Lamplight2026/patchers/encoderin.maxpat:165,231` (`serial #1`, `serial #2`) and `EncoderTester.maxpat:1415` | **no** | **LIVE** |
| `TreeHouse_Controllers/` | ESP32-S3 DevKitC-1 (4 MB), PlatformIO/Arduino C++17, NeoPixelBus; `env:native` for Unity tests | 5 locations: SK6812 strips, PWM MOSFET dimmers, cap-discharge arc trigger (ADR-0020/0021) | 3,357 (src 807, lib 1,031, test 1,113, ini 112 …) | 3 (2026-09-06 → 2026-10-27) | `docs/agents/firmware.md`, `docs/TreeHouse.md`, ADR-0020/0021, `scripts/hooks/firmware_config_gen.py`, `ESP32S3_SignsOfLife/README.md` | **yes** (174 lines, good) | **LIVE** |
| `ESP32S3_SignsOfLife/` | ESP32-S3, PlatformIO/Arduino, Adafruit NeoPixel | Board bring-up: 8-px strip RGBW cycle + onboard LED + serial heartbeat + `esp_reset_reason()` | 125 (88 `main.cpp` + 37 ini) | 1 (2026-09-06) | `TreeHouse_Controllers/README.md:58-60` only | yes (101 lines) | **LIVE diagnostic**, but a hello-world |
| `TreeHouse_PicoLEDs/` | RP2040 Pico, MicroPython + PIO | SK6812 pixel sink over USB JSON lines (ADR-0010) | 64 | 1 (2026-05-07) | `docs/agents/firmware.md:48` ("superseded"), ADR-0010, ADR-0020, `architecture.md:18`, docstrings in `Club_Pico/main.py:18`, `HouseSwarming_Pico/main.py:18` | **no** | **SUPERSEDED (ADR-0020) but still wired on the Pi** — see below |
| `HouseSwarming_Pico/` | Pico, MicroPython + PIO | 3 standalone SK6812 strips: fireplace flicker + 2 static warm-white overheads, no host | 106 | 1 (2026-05-29 "stopgap firmware for house lights") | **zero** | **no** | **DEAD** — functionally replaced by `TreeHouse_Controllers/src/targets/swannatopia.h` (fire + incandescent overhead + chandelier) |
| `Club_Pico/` | Pico, MicroPython + PIO | 2 standalone SK6812 strips (magenta/cyan bands, cool-white comet) + PWM superbright LED, no host | 132 | 1 (2026-05-29) | **zero** | **no** | **DEAD** — replaced by `targets/jess.h` (2 `Rave` strips + `Flash` MOSFET) |
| `Fungi_Pico/` | Pico, MicroPython | 1 PWM filament gamma-corrected sine breathe 30–80 %, 16 s, no host | 45 | 3 (2026-05-29 → 2026-05-30 "fix fungi/dormer") | **zero** | **no** | **DEAD** — replaced by `targets/julia.h` (`Wander` 40–80 %) and `targets/dormer.h` (`Breathe` 12.5 s 40–80 %) |

Also deleted from history already: `Firmware/Dynamixel_Config/` (removed 2026-04-04, `7581a4b`). No `Firmware/README.md` at the top level, so a reader has no map of these nine directories.

### 1a. The three "stopgap" Picos are dead code

`Firmware/Club_Pico/main.py:1`, `Firmware/HouseSwarming_Pico/main.py:1`, `Firmware/Fungi_Pico/main.py:1` each open with `"... standalone Pico light controller (stopgap)"`. They were a one-day fix (2026-05-29/30) for the TreeHouse house lights before any host-driven path existed. Each duplicates the same 15-line PIO SK6812 driver (`_sk6812`, `Strip`) copy-pasted from `TreeHouse_PicoLEDs/main.py:8-22`. Nothing in `ShowControl/`, `docs/`, `scripts/` or any ADR mentions them. The ESP32-S3 project (ADR-0020, amended ADR-0021 to run standalone — i.e. exactly the "stopgap" behaviour, but on the new hardware) covers every one of their roles, location by location. **Delete all three (283 LOC, 3 files).**

### 1b. `TreeHouse_PicoLEDs` — superseded on paper, still deployed in code

ADR-0020 `Consequences`: "`Firmware/TreeHouse_PicoLEDs/` is superseded. It stays in the tree until the ESP32-S3 hardware is physically installed, then is removed along with `pico_driver.py` and the `pico_*` blocks in `settings.json`." None of that removal has happened:

- `ShowControl/TreeHouse/main.py:24` `from pico_driver import PicoDriver`; `:149` `driver = PicoDriver(config.pico.port, config.pico.baud)`; `:150` connects unless `--no-pico`.
- `ShowControl/TreeHouse/deploy/treehouse.service:14` `ExecStart=/usr/bin/python3 main.py --config settings.json` — no `--no-pico`, so production still opens the Pico.
- `ShowControl/TreeHouse/settings.json:2,7` still has `pico_dioramas` / `pico_structure` blocks (ADR-0010 names), while `main.py:149` reads a single `config.pico` — flag to the ShowControl auditor; it looks like the two-Pico split from ADR-0010 was never finished in `main.py`.
- `docs/TreeHouse.md:15` (last edited 2026-09-06) says the Picos are "still wired until the ESP32-S3 hardware is installed".

Whether the ESP32 boards are physically in the house is not knowable from the repo (`garage.h:22` still says pins are placeholders; ADR-0021 is dated 2026-10-27 and speaks of "this round of the show"). **Verdict: keep until the owner confirms hardware; then delete `TreeHouse_PicoLEDs/`, `pico_driver.py`, the `pico_*` settings, `--no-pico`, and the udev section of `docs/TreeHouse.md:164-171` in one PR.** Note ADR-0010 says udev rules are "generated by `scripts/install-services.sh`" — `grep -n "pico\|udev\|treehouse-" scripts/install-services.sh` returns nothing. That claim was never true in main.

### 1c. `ESP32S3_SignsOfLife` is a hello-world — a deliberate, documented one

`src/main.cpp:1-6`: "the smallest thing that proves the board boots … No WiFi, no OSC, no Garden State, no config headers." Its README is a genuinely useful boot-loop/brownout triage guide (`README.md:55-87`) and is cross-referenced from `TreeHouse_Controllers/README.md:58`. But it duplicates the entire ESP32-S3 `platformio.ini` board block (`ESP32S3_SignsOfLife/platformio.ini:16-29` ≡ `TreeHouse_Controllers/platformio.ini:20-32`, same 4 MB flash workaround comment verbatim) plus a second `.vscode/` and `.gitignore`. **Verdict: fold it into `TreeHouse_Controllers` as `[env:signsoflife]` with `build_src_filter = +<SignsOfLife.cpp>` (or similar) and move the triage README into a "Bring-up" section of the main README; delete the directory (5 files → 1 .cpp).** One PlatformIO project, one `.vscode`, one place to look.

### 1d. `firmware_config_gen.py` — generates one header, the docs claim two

`scripts/hooks/firmware_config_gen.py:14-19`:

```
Currently generated:
  Firmware/TreeHouse_Controllers/include/net_config.h   (ADR-0020)
TODO: generate Firmware/FlowerBeds_Follow_ServoController/config.h too.
```

Only `TREEHOUSE_HEADER` is written (`:26-28`, `generate()` `:90-94`). Consumers: `TreeHouse_Controllers/src/targets/target.h:7` and `src/Net.cpp:6` `#include "net_config.h"`. The committed `include/net_config.h` matches `ShowControl/network.json` (`firmware.treehouse_*` 192.168.1.60-64, port 9000; `lan` block) — it is a generated-but-committed file, by design.

The FlowerBeds sketch does **not** consume any generated header. `FlowerBeds_Follow_ServoController.ino:25-27` hardcodes:

```
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0x15, 0x01 };
IPAddress ip(192, 168, 1, 51);     // set for your LAN
const uint16_t localPort = 9000;
```

plus `HB_PORT = 9100` at `:35`. That is `network.json` `firmware.flowerbeds_controller_2` typed by hand, and a direct violation of AGENTS.md constraint #3. Both `docs/agents/firmware.md:8` ("IP and MAC come from a generated `config.h`") and `docs/agents/configuration.md:113` ("Firmware reads addresses from a generated `config.h`") describe a mechanism that does not exist. Either finish the TODO (render `config.h` for both `flowerbeds_controller_1/2`, `#include "config.h"` in the sketch, gitignore it) or fix the docs. The first is ~20 lines of Python and makes the second-board MAC/IP collision risk (`firmware.md:10`) go away.

### 1e. `TreeHouse_Controllers/lib/*` and `test/`

All five libs are used (`#include` graph): `Patterns` ← `GardenState`, `Rng`, `Weld`; `GardenState` ← `OscRx`; `Weld` ← `Rng`; `src/` includes `GardenState`, `OscRx`, `Patterns`, `Outputs`, `Net`. `lib/` contains only `<cmath> <cstddef> <cstdint> <cstring>` — the "Arduino-free" claim in `firmware.md:28` holds. No `library.json` manifests (PlatformIO infers; fine).

Dead code inside `lib/Patterns`: `PatternId` has 11 values (`Patterns.h:33-48`); targets use 7 (`Breathe, Fire, Flash, Incandescent, Rave×2, Wander, Weld`). `Solid`, `Chase`, `Filament` are referenced only by tests; **`Mycelium` (`Patterns.h:37`, `Patterns.cpp:255`) is referenced by no target, no test, no self-test** — it is the old Pico-era diorama pattern carried over. Candidate for removal with the other three if the owner agrees they are not planned.

Tests (`pio test -e native`): 51 cases across 4 suites — `test_garden_state` (7: Fabric address folding, clamping, one-shot blow-up, mode strings, staleness), `test_oscrx` (8: float/string/int/argless parsing, malformed packets, bundles, lying bundle sizes), `test_patterns` (30: signal bag, dim/inactive, stale breathe, blow-up, flash, chase, fire, breathe, wander, weld, rave, gamma), `test_weld` (6: session/burst/tap gaps, recharge guarantee, seeding, millis rollover). Coverage of the host-testable logic is good. **They are not run in CI**: `.github/workflows/tests.yml` installs Node + Python only; `Makefile` runs `node --test` and `pytest`; no `pio` anywhere outside `firmware.md:28`.

Tracked junk: `Firmware/TreeHouse_Controllers/.vscode/c_cpp_properties.json` (538 lines, 68 KB, **483 lines containing `/home/charliehuge/...`**) and `.vscode/launch.json` (44 lines, absolute `/home/charliehuge/projects/...` paths, header says "AUTOMATICALLY GENERATED FILE"). Both are listed in the project's own `.gitignore:3-5` and `git ls-files -i -c --exclude-standard` confirms they are tracked anyway (added in `67b2098`, re-touched in `2ce5f20`). `git rm --cached` them. The 24th-largest file in the whole repo is a PlatformIO IntelliSense cache.

### 1f. READMEs

Only 2 of 9 firmware dirs have one. `FlowerBeds_Follow_ServoController`, `TreeHouse_BranchController`, `PlayingThePipes_EncoderPico` are live production firmware whose required libraries and flashing procedure live only in `docs/agents/firmware.md` / `docs/PlayingThePipes.md`. Each needs a 10-line README (board, libs, what it listens to, how to flash) or the directory is not self-describing.

---

## 2. Prototypes

| Dir | What | Files / lines | Commits | Code shared with ShowControl? | Verdict |
|---|---|---|---|---|---|
| `ForgeAndFlora/forge_and_flora.py` | Pico MicroPython bench tester for the Forge & Flora diorama: 6-px "forge" strip (amber flicker + blue-white arc flash) and 4-px "flora" strip (green/yellow breathe) | 1 / 121 | 1 (2026-05-07 "add fnf tester firmware") | **No.** `grep -rlw` of its symbols (`write_pixel`, `update_forge`, `update_flora`) in `ShowControl/`+`IIVision/` → 0 hits. | **DELETE** |
| `GlowPanels/` | Fabrication notes for two acrylic "mycelium glow panel" construction methods (side-lit vs back-lit frosted) + a 110-LOC generic breathing/gradient Pico script | 4 / 474 (3 READMEs = 364 lines) | 2 (2026-04-20, 2026-05-07 "update panel prototype firmware with LED counts for Mycelium") | **No code.** But `firmware/panel_gradient.py:24` `NUM_LEDS = 224` matches `ShowControl/TreeHouse/settings.json:49` Mycelium `led_count: 224` — this is the build log for the Mycelium diorama that now ships in production. | **MOVE the two build READMEs** to `docs/` (fabrication record), **delete** `panel_gradient.py` and the top README |
| `TouchTest/` | Orbbec Gemini 336L depth-touch experiments for FundingCAPTCHA: `touch_test.py` (815 lines, pygame calibrator: BG model → 4-corner perspective cal → live grid), `captcha_touch.py` (417, 4×4 Schmitt-trigger grid detector emitting OSC `/captcha/touch/*`), `ir_test.py` (102, IR viewer) | 5 / 1,347 | 1 (2026-05-10 "Add camera touch calibrator (#79)") | **No.** 14 distinctive symbols (`BgCal`, `CornerCal`, `GridTouchDetector`, `ENTER_MM`, `FRAMES_TO_ENTER`, `_corner_contact_point`, …) → 0 hits in `ShowControl/`+`IIVision/`. Production FundingCAPTCHA uses `body_blobs.py`/`body_grid.py`/`silhouette.py` (ADR-0013) and the Fabric schema (ADR-0007) has no `/captcha/touch/*`. | **DELETE** |

`ShowControl/TreeHouse/test_forge_and_flora.py` tests the **production** module: `:5` `from displays.effect import ForgeAndFloraConfig, ForgeAndFloraDisplay` (`ShowControl/TreeHouse/displays/effect.py:11,22`). It has nothing to do with `Prototypes/ForgeAndFlora/`. Note the irony: the Pi-side `ForgeAndFloraDisplay` is itself on the chopping block once the Pico path goes (section 1b), and the ESP32 `Weld` pattern (`lib/Patterns`) is the third-generation implementation of the same idea.

`pytest.ini` `testpaths = ShowControl IIVision scripts` — nothing under `Prototypes/` is collected or tested. No doc anywhere (`docs/`, `README.md`, `CONTEXT.md`, `AGENTS.md`) mentions `Prototypes/`. `Prototypes/FundingCAPTCHA/` was already deleted on 2026-04-30 (`3dd3d06`), so there is precedent for retiring a prototype once it graduates.

Whole directory: 10 files, 1,942 lines, 96 KB → 0 files if the GlowPanels READMEs move to `docs/`.

---

## 3. PlayingThePipes

### 3a. Which patch is the show?

**`Lamplight2026/patchers/Lamplight2026.maxpat`** is the current show patch — by elimination and evidence:

- Newest: `a25d6a5` 2026-10-27 "Ptp ll26 (#155)" touched only `Lamplight2026/`; it was created in `4b72fbf` 2026-10-01 "Ptp v3 (#153)" (38 files added).
- It is the only project that contains the encoder-Pico serial reader: `Lamplight2026/patchers/encoderin.maxpat:165` `"serial #2"`, `:231` `"serial #1"` (two Picos, matching ADR-0014), and `fake_encoder.maxpat` for bench use.
- `Lamplight2026.maxproj` is the only project with a dependency on another project (see 3c).

**`docs/PlayingThePipes.md` does not say so.** It names `ShowControl\PlayingThePipes\PlayingThePipes.maxpat` at `:11`, `:43`, `:93`, as does `docs/bootstrap.md:173,198`. That file has **never existed on `main`**. The only place it ever existed is `ShowControl/PlayingThePipes/Music/PlayingThePipes.maxpat` on the unmerged branch `origin/claude/max-music-system-stub-z2Qs0` (`f486680`, 2026-04-17, "Add Playing The Pipes music system Max patch stubs", 8 stub patchers). `docs/PlayingThePipes.md` was written once (2026-05-25, `0b9f044`) against that stub and never updated through three rounds of real patches.

Other doc claims vs patch reality: "Max/RNBO" (`PlayingThePipes.md:11`, `README.md:23`, ADR-0014 "RNBO patch") — `grep -rl 'rnbo~'` across all `.maxpat` → **0 files**. The engine is `grainflow~` (third-party Grainflow package), `groove~`, `mc.*~`, and two Ableton device objects `abl.device.reverb~`, `abl.device.spectraltime~` (Max 9 `abl.*` package). None of these dependencies is documented anywhere. "`/pipes/activity` is planned but not wired" — true: no `udpsend` in any patch.

### 3b. The three projects

| Project | Files / lines / tracked KB | LFS media | Commits | Reachable from its top patch | Verdict |
|---|---|---|---|---|---|
| `Lamplight2026/` | 42 / 11,804 / 660 KB | 33 files, 114 MB | 2 (2026-10-01, 10-27) | 6 local patchers (`encoderin`, `fake_encoder`, `isactive`, `knobgrain`, `knobvelocity`, `midilearn`) + 2 from MakeNoiseDay | **KEEP** (current show) |
| `MakeNoiseDay/` | 26 / 16,557 / 576 KB | 0 | 3 (2026-09-09, 09-25 "Pipes 0coast", 10-01) | top patch `MakeNoiseDay.maxpat` uses 5 of its 15 patchers + 0 of 2 `.gendsp`; **Lamplight2026 uses exactly 2: `scaleclip.maxpat` (169 lines) and `wakemove.maxpat` (210 lines)**, both via `knobgrain.maxpat` | **Copy those 2 files into `Lamplight2026/patchers/`, then DELETE** (24 files, 16,178 lines) |
| `Pipes Prototype 3/` | 110 / 133,349 / 6,832 KB | 24 files, 112 MB | 1 (2026-09-09 "carolina tweaks (#141)", 110 files added at once) | top patch uses 14 of 62 patchers; **Lamplight2026 references nothing in it** (transitive closure over `text` and bpatcher `name` fields) | **Tag `archive/pipes-prototype-3`, DELETE from main** |
| `EncoderTester.maxpat` | 1 / 1,754 / 72 KB | — | 1 (2026-05-22) | — ; has `serial h` at `:1415`, `/enc` parsing | KEEP (referenced by `PlayingThePipes.md:47,92`) |
| `health_server.py`, `requirements.txt` | 2 / 57 | — | — | — | KEEP (NSSM service, `bootstrap.md:185-191`) |

`MakeNoiseDay/other/README.md` + `other/LICENCE` identify it as a personal modular-synth Max library (MIT 2017, with streaming links) dropped into the repo wholesale; it is a vendored dependency, not show code. `Lamplight2026.maxproj:20-40` pins its three MakeNoiseDay dependencies with `"bootpath": "~/Projects/CommunityGarden/ShowControl/PlayingThePipes/MakeNoiseDay/patchers"` — a machine-specific absolute path, and one of the three (`autograin.maxpat`) is referenced by **no** Lamplight2026 patcher (stale `.maxproj` entry). Copying `scaleclip`/`wakemove` in and dropping the singleton entries makes Lamplight2026 self-contained.

### 3c. Duplicates inside `Pipes Prototype 3/patchers/`

The ten `X.amxd` / `X.maxpat` pairs with identical line counts (Dual Harmonizer 6,775; Fragulator 910; Max AutoFilter 2,086; Max AutoRingMod 1,373; Max CombFilterMulti 1,494; Max EqShelving 2,312; Max SpectralHarm 3,875; Noyzckippr 3,721; Phone Filter 1,547; Speed Shifter 1,643) are **the same bytes plus a 20-byte Max-for-Live `ampf…ptch` wrapper**: `cmp` differs, `diff` reports 0 differing lines, and Python confirms `amxd[20:] == maxpat` exactly (e.g. `Fragulator.amxd` 35,787 B vs `.maxpat` 35,767 B). Both halves are binary-framed (`mx@c` header, `flag`/`mdat` trailer) exported Ableton devices, not hand-written patchers. That is 1,744 KB of `.amxd` duplicated as 1,744 KB of `.maxpat` — 33 % of the repo's tracked bytes is one copy of ten Live devices, and another 16 % is the second copy. `Pendulum.amxd` (152 KB) has no twin.

Also in P3: `fragment`/`fragmentOLD`, `pendulum`/`pendulumOLD`, `spectralharm`/`spectralharmOLD` (near-identical: 50/101/92 differing lines), nine `data/*.amxd_20260902.maxsnap` snapshot copies beside their `*.amxd.maxsnap` originals (4–24 line deltas), and 36 patchers reachable from nothing (full list in the appendix). `Lamplight2026/patchers/knobgrain.maxpat` shares 751 sorted lines with P3's `bp.rgrain.maxpat` — the useful part was already ported.

### 3d. Media

All 57 `.wav`/`.png` under `PlayingThePipes/` are **Git LFS pointer files** (`.gitattributes` tracks `*.wav *.png *.jpg *.mp3 …`), 3 lines each; the objects are not even fetched in this clone (`git lfs ls-files` shows `-` for every one). Declared sizes:

- `Lamplight2026/media/`: 33 files, **114.3 MB**. Referenced by name from Lamplight2026 patchers: 13 files, 73 MB. **Unreferenced by name: 20 files, 41 MB**, including `tone.04.wav` alone at 22.3 MB, `scrapes.wav` 5.6 MB, `waterBell1.wav` 4.2 MB, two `.png` logos/banners (0.7 MB). Caveat: Max can load buffers by message at runtime, so "unreferenced by static grep" needs a 5-minute confirmation in Max before deletion. `grainflow.wav` is referenced (`Lamplight2026.maxpat`) but not present in `media/` — either a Grainflow-package sample or a missing asset.
- `Pipes Prototype 3/media/`: 24 files, **112.0 MB — every one byte-identical to its Lamplight2026 twin** (`cmp` on all 24 pointer files). Pure duplication.

Is 226 MB of samples appropriate here? LFS keeps them out of the pack (`.git` is 2.6 MB), so clone cost is fine, but it costs LFS storage/bandwidth quota and every `git lfs pull` on a show machine drags 112 MB of dead duplicates. The deployment path (`PlayingThePipes.md:71-74`: `git push … pipes:CommunityGarden` to the Windows host) does need the samples to travel with the patch, which argues for keeping the **referenced** Lamplight2026 samples in LFS (or in the private assets repo, mirroring how `ShowControl/FundingCAPTCHA/images/private/` is handled — see AGENTS.md #6). Either way: delete the P3 copies (−112 MB LFS), confirm-then-delete the 20 unreferenced Lamplight files (−41 MB), leaving ~73 MB that is actually played.

### 3e. Verdict per project

1. **Lamplight2026** — keep in repo; make self-contained (copy 2 patchers in, fix `.maxproj` bootpaths); add a README naming it as the show patch and listing externals (Grainflow, `abl.*`, two serial COM ports); prune unreferenced media after confirming in Max.
2. **MakeNoiseDay** — delete after the 2-file copy (−24 files, −16,178 lines, −560 KB). If the author wants it preserved, it belongs in its own repo (it already has its own README/LICENCE).
3. **Pipes Prototype 3** — `git tag archive/pipes-prototype-3 <HEAD>` then delete (−110 files, −133,349 lines, −6.8 MB tracked, −112 MB LFS). It is 82 % of the repo's lines and nothing live depends on it.

---

## 4. TouchOSC

`TouchOSC/FlowerBedTester.tosc` — 4 KB zlib-compressed TouchOSC-mk2 layout (16.5 KB XML when inflated). Contents: one GROUP with 4 fader-style controls, each OSC-enabled and named `cg/ff/rot`, sending `/<name>` with a constant INTEGER argument (motor id) + the control value — i.e. a hand controller for `/cg/ff/rot [int motor_id, float deg]`, matching `FlowerBeds_Follow_ServoController.ino:82,193-199`. 3 commits (2026-02-16 → 2026-04-17), none since. Referenced by `docs/agents/running-and-testing.md:69` ("validate with `TouchOSC/FlowerBedTester.tosc`") and `architecture.md:19`. ADR-0005:23 and ADR-0007:27,91 mention TouchOSC as a possible operator surface for TreeHouse; no such layout exists.

Verdict: **LIVE but opaque.** Keep, but it should not be a top-level directory for one 4 KB binary. Move to `ShowControl/FlowerBeds/tools/FlowerBedTester.tosc` (next to `diag.py`, which does the same job from Python) with a 5-line README (what it sends, which host/port to set in the app — `network.json` `firmware.flowerbeds_controller_*`). Alternatively, if `diag.py` has made it redundant, delete it and fix `running-and-testing.md:69`.

---

## 5. Repo-size hygiene

Tracked bytes by extension (`du -k` over `git ls-files`, basename-safe):

| Ext | KB | Files | Note |
|---|---|---|---|
| `.maxpat` | 6,012 | 78 | 5,500+ KB of it under `Pipes Prototype 3/` |
| `.amxd` | 1,744 | 11 | all `Pipes Prototype 3/`; 10 are twins of `.maxpat` files |
| `.py` | 908 | 92 | |
| `.md` | 556 | 66 | |
| `.glsl` | 248 | 24 | |
| `.wav` (LFS pointers) | 212 | 53 | 226 MB behind them |
| `.json` | 196 | 23 | 68 KB is `c_cpp_properties.json` |
| `.maxsnap` | 92 | 23 | all P3; 9 are dated duplicates |
| everything else | < 700 | | |

Top 20 largest tracked files: **all 20 are under `ShowControl/PlayingThePipes/`** (19 in `Pipes Prototype 3/patchers/`, 1 is `Lamplight2026.maxpat` at 408 KB; `MakeNoiseDay.maxpat` 212 KB is #5). #1 is `Pipes Prototype 3/patchers/Pipes Prototype 3.maxpat` at 2,196 KB / 45,901 lines — 21 % of the repo by bytes, 28 % by lines. `Firmware/TreeHouse_Controllers/.vscode/c_cpp_properties.json` (68 KB) is #24.

Should be untracked / gitignored:

- `Firmware/TreeHouse_Controllers/.vscode/c_cpp_properties.json`, `.vscode/launch.json` — already matched by that project's `.gitignore`, tracked anyway (`git ls-files -i -c --exclude-standard`). `git rm --cached`.
- Root `.gitignore` has no `.pio/` or PlatformIO `.vscode` entries; it relies on per-project `.gitignore`s (`TreeHouse_Controllers/.gitignore`, `ESP32S3_SignsOfLife/.gitignore`). Add `**/.pio/`, `**/.vscode/c_cpp_properties.json`, `**/.vscode/launch.json`, `**/.vscode/ipch` at the root so the next PlatformIO project cannot repeat this.
- `Prototypes/TouchTest/.gitignore` (`calibration.npz`) goes away with the directory.
- `*.maxsnap` dated snapshots (`*_20260902.maxsnap`) are editor state, not source; gone with P3.

Not a problem: `.git` pack is 1.77 MB; no `.pyc` tracked; `ShowControl/FundingCAPTCHA/deploy/private-assets.example.env` is an example file, not a secret. `include/net_config.h` is generated-and-committed by design.

---

## 6. Docs drift

| Doc | Line(s) | Says | Reality |
|---|---|---|---|
| `docs/PlayingThePipes.md` (1 commit, 2026-05-25) | 11, 43, 93 | Show patch is `PlayingThePipes.maxpat`; "Max/RNBO" | File never existed on `main` (only on unmerged `origin/claude/max-music-system-stub-z2Qs0`). Show patch is `Lamplight2026/patchers/Lamplight2026.maxpat`. No `rnbo~` in any patch; engine is `grainflow~`/`groove~`/`abl.device.*`. |
| `docs/PlayingThePipes.md` | 50-57 | COM port table "TBD" | Still TBD five months later; `encoderin.maxpat` uses `serial #1`/`#2` arguments, so COM names are patcher args, not hardcoded — doc should say that. |
| `docs/bootstrap.md` (2026-09-06) | 16, 173, 198 | "Max/RNBO audio I/O"; "Record COM numbers in `PlayingThePipes.maxpat`"; "Open `…\PlayingThePipes.maxpat`" | Same non-existent file. |
| `README.md` | 23 | "Max/RNBO music system" | No RNBO. |
| `docs/agents/firmware.md` (2026-10-27) | 8 | FlowerBeds "IP and MAC come from a generated `config.h`" | `.ino:25-27` hardcodes them; generator has it as `TODO` (`firmware_config_gen.py:19`). |
| `docs/agents/firmware.md` | whole file | Lists 4 firmware dirs | 9 exist; `Club_Pico`, `HouseSwarming_Pico`, `Fungi_Pico`, `ESP32S3_SignsOfLife`, `PlayingThePipes_EncoderPico` are absent. |
| `docs/agents/configuration.md` (2026-05-22) | 113 | "Firmware reads addresses from a generated `config.h`" | Only `net_config.h` for TreeHouse_Controllers is generated. |
| `docs/agents/architecture.md` (2026-05-22) | 15-19 | Tree lists 3 firmware dirs, `TouchOSC/`, no `Prototypes/` | 9 firmware dirs, `Prototypes/` exists with 3 subdirs. |
| `docs/agents/architecture.md` | 26 | "`pytest.ini` — testpaths = ShowControl IIVision" | `pytest.ini` says `ShowControl IIVision scripts`. |
| `docs/TreeHouse.md` (2026-09-06) | 14, 196 | "4× ESP32-S3 … Swannatopia, Julia, Jess, Dormer" / "Four ESP32-S3 controllers" | Five since ADR-0021 (Garage, 192.168.1.64); `settings.json` `locations.controllers` lists 5; `net_config.h:29-32` has `GARAGE`. |
| `docs/TreeHouse.md` | 15-17, 164-171, 234 | Pico A/B wired, udev symlinks, "LEDs dark → check `/dev/treehouse-pico-a`" | Consistent with code (`main.py:149`) but contradicts ADR-0020's stated removal; the repo cannot tell which is true on site. |
| ADR-0010 | header | `Status: Accepted` | Superseded by ADR-0020 (which says so in *its* header); ADR-0010 should carry `Superseded by ADR-0020`. |
| ADR-0010 | "Stable device names via udev" | "Udev rules are generated by `scripts/install-services.sh`" | No udev/pico content in that script, in any revision on `main`. |
| ADR-0014 | Decision | "routes events into the RNBO patch" | No RNBO. Protocol (`/enc BOARD ENC DELTA`) and pin map match `PlayingThePipes_EncoderPico/main.py:11-48` exactly — the rest is accurate. |
| ADR-0020 | Consequences | PicoLEDs/`pico_driver.py`/`pico_*` removed when hardware installed; `location_sender.py` "additive" | Nothing removed; both paths still run (section 1b). Also says "four environments" — amended by ADR-0021 (header notes this; fine). |
| ADR-0021 | all | `kFollowGardenState` in `src/main.cpp`; Garage pins placeholders; `treehouse_garage` 192.168.1.64 | All verified: `main.cpp:48`, `garage.h:22`, `network.json`, `net_config.h:29-32`. **Accurate.** |
| ADR-0005 | all | USB JSON-lines, same protocol as `pico_driver.py` | Matches `TreeHouse_BranchController.ino:5-11`. **Accurate.** |
| `Firmware/TreeHouse_Controllers/README.md` | 164 | "Stop sending for 10 s and the channels drop to idle breathe" | Only when `kFollowGardenState == true`; the README does qualify this at :151, but :164 reads as unconditional. Minor. |

---

## Ranked recommendations

1. **Delete `ShowControl/PlayingThePipes/Pipes Prototype 3/`** after tagging `archive/pipes-prototype-3`. −110 files, −133k lines, −6.8 MB tracked (64 % of repo), −112 MB LFS. Nothing live references it.
2. **Collapse `MakeNoiseDay/` into `Lamplight2026/`**: copy `scaleclip.maxpat` + `wakemove.maxpat` into `Lamplight2026/patchers/`, drop the three `singleton.bootpath` entries from `Lamplight2026.maxproj`, delete `MakeNoiseDay/`. −24 files, −16k lines. Then write `ShowControl/PlayingThePipes/README.md` naming Lamplight2026 as the show patch and listing externals.
3. **Fix `docs/PlayingThePipes.md`, `docs/bootstrap.md`, `README.md`**: replace every `PlayingThePipes.maxpat` with `Lamplight2026/patchers/Lamplight2026.maxpat`; drop "RNBO". These docs currently send an operator to a file that has never existed.
4. **Delete `Firmware/Club_Pico`, `HouseSwarming_Pico`, `Fungi_Pico`** (−283 LOC, zero references, superseded by ESP32 targets) and **`Prototypes/ForgeAndFlora`, `Prototypes/TouchTest`** (−1,468 lines, zero shared code). Move the two GlowPanels build READMEs to `docs/`, delete the rest of `Prototypes/`.
5. **`git rm --cached Firmware/TreeHouse_Controllers/.vscode/{c_cpp_properties,launch}.json`** and add PlatformIO patterns to the root `.gitignore`. 483 lines of another machine's home directory are in the repo.
6. **Finish `firmware_config_gen.py`'s TODO** so `FlowerBeds_Follow_ServoController` includes a generated `config.h` instead of hardcoding MAC/IP (`.ino:25-27`, constraint #3 violation) — or correct `firmware.md:8` and `configuration.md:113`.
7. **Fold `ESP32S3_SignsOfLife` into `TreeHouse_Controllers`** as a `signsoflife` environment; one PlatformIO project, one triage README.
8. **Resolve the Pico question on site**: if the ESP32 boards are installed, execute ADR-0020's removal list (`TreeHouse_PicoLEDs/`, `pico_driver.py`, `pico_*` settings, `--no-pico`, `docs/TreeHouse.md:15-17,164-171`); if not, update `docs/TreeHouse.md:14,196` to five controllers and leave the rest. Mark ADR-0010 `Superseded by ADR-0020`.
9. **Prune `Lamplight2026/media/`**: confirm in Max, then delete the 20 files (41 MB LFS) no patcher names, starting with `tone.04.wav` (22 MB). Decide whether the remaining ~73 MB lives in LFS or the private assets repo.
10. **Add `Firmware/README.md`** (one table: dir → board → what it drives → live/retired) and 10-line READMEs for `FlowerBeds_Follow_ServoController`, `TreeHouse_BranchController`, `PlayingThePipes_EncoderPico`. Add `pio test -e native` to CI or state in `firmware.md` that it is manual.
11. Move `TouchOSC/FlowerBedTester.tosc` to `ShowControl/FlowerBeds/tools/` with a README, or delete it in favour of `diag.py`. Remove `PatternId::Mycelium` (and `Solid`/`Chase`/`Filament` if unplanned) from `lib/Patterns`.

Net effect of 1–5 alone: roughly **−149 files, −152k lines, −7.5 MB of 10.6 MB tracked (≈71 %), −112 MB LFS**, with every surviving directory having a README that says what it is.

---

## Appendix A — `Pipes Prototype 3/patchers/` files reachable from nothing

`Dual Harmonizer.maxpat`, `Fragulator.maxpat`, `M4L.bal2~.maxpat`, `M4L.comb2.voice~.maxpat`, `M4L.envfol~.maxpat`, `M4L.pan2~.maxpat`, `M4L.transp.pfft~.maxpat`, `M4L.vdelay~.maxpat`, `Max AutoFilter.maxpat`, `Max AutoRingMod.maxpat`, `Max CombFilterMulti.maxpat`, `Max EqShelving.maxpat`, `Max SpectralHarm.maxpat`, `Noyzckippr.maxpat`, `Phone Filter.maxpat`, `Speed Shifter.maxpat`, `autofilter.maxpat`, `bloom.maxpat`, `bloomplay.maxpat`, `bp.rgrain.maxpat`, `cctoplay2.maxpat`, `frag.stutter_Pshift22~.maxpat`, `fragment.maxpat`, `fragmentOLD.maxpat`, `knobspeed.maxpat`, `midilearn.maxpat`, `noise.maxpat`, `pend.spread.maxpat`, `pendulumOLD.maxpat`, `pluggo.dryWet2~.maxpat`, `pluggo.dryWet3~.maxpat`, `rchoose.maxpat`, `rchoosef.maxpat`, `spectralharmOLD.maxpat`, `speed.rsc2~.maxpat`, `transRatio.maxpat`. (The `.amxd` devices are loaded by `amxd~` at runtime and so are not in this static list.)

## Appendix B — `MakeNoiseDay/` files reachable from nothing (including from Lamplight2026)

`code/clock.gendsp`, `code/euclidseq.gendsp`, `patchers/Euclid.maxpat`, `ImprovBox.maxpat`, `ImprovBox2.maxpat`, `chordseq.maxpat`, `euclid_internal.maxpat`, `euclid_ui.maxpat`, `isalive.maxpat`, `lfo~.maxpat`, `miditocv.maxpat`, `scaleseq.maxpat`, `synclfo~.maxpat`, `temposlider.maxpat`, `trigger~.maxpat`, `volseq.maxpat`. Used only by `MakeNoiseDay.maxpat` itself: `autograin`, `scalemapper`. Used by Lamplight2026 (via `knobgrain.maxpat`): `scaleclip`, `wakemove`.

## Appendix C — method notes

- LOC = `wc -l` over `git ls-files`; "code LOC" excludes `.md`, `.json`, `.gitignore`.
- Commit counts/dates re-run after `git fetch --unshallow` (207 commits from 2026-01-24).
- Max reachability: parsed each `.maxpat` as JSON, collected `box.text` first tokens and bpatcher `box.name`, followed edges to same-named local files transitively. Binary-framed `.maxpat`/`.amxd` were compared with `cmp`, `diff` and byte-offset search in Python.
- Reference greps excluded `.git/` and `__pycache__/`.
