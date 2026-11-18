# ADR-0015 — FlowerBeds GUI Layout Tool

**Status:** Accepted
**Supersedes:** [ADR-0009](0009-aruco-auto-layout-for-flower-modules.md)

## Context

ADR-0009 introduced ArUco marker–based layout calibration: place printed tags at module
registration points, run `--layout-calibrate`, write `layout_calibrated.json`. This required:

- An overhead Orbbec RGB camera pass
- Printing and placing 12 large (40 cm) markers
- `opencv-python-headless` dependency
- A `layout_calibrated.json` override file loaded at runtime
- `marker_id` fields in `settings.json` to map tags to modules

In practice the overhead camera is already stowed when the FlowerBeds laptop is out for
config work, the markers are cumbersome, and the visual-feedback loop was poor — you
couldn't easily see whether the resulting layout looked right before running the show.

The replacement is a purpose-built Windows GUI tool that runs on the operator's laptop,
connects directly to the show network, and lets the operator drag-place modules visually,
verify the layout, aim individual clusters, and check controller reachability — all before
touching `settings.json`.

## Decision

### Tool location and stack

`ShowControl/FlowerBeds/layout_tool.py` — a standalone FastAPI server with an embedded
HTML/JS browser client. Launched with `python layout_tool.py`, opens on port **8764**.
Shares the existing `requirements.txt` (FastAPI, uvicorn, python-osc already present).
`opencv-python-headless` is removed.

### Config file contract

The tool reads and writes **only `coordinator.modules[]`** in `settings.json`. All other
fields (`stabilizer`, `cameras`, `calibration_frames`, etc.) are preserved verbatim.
Before any write, `settings.json` is copied to `settings.json.bak`. The operator saves
explicitly via a Save button; there is no autosave.

The `layout_calibrated.json` override file and all `apply_layout_overrides` machinery are
removed. `settings.json` is the single authoritative source of layout at runtime.

The `marker_id` field is removed from `ModuleConfig`. A `name` field (string) is added;
default `"Module N"` (user-editable in the GUI).

### Module and cluster defaults

The tool starts a new layout with 12 modules, all placed at the world origin, named
`"Module 1"` … `"Module 12"`. The operator drags each module to its installation position.

Each module defaults to 4 clusters with the standard hardware offsets (cm, relative to
module registration point, `[X_right, Y_forward, Z_up]`):

| Cluster | Default offset | Default motor ID |
|---------|---------------|-----------------|
| 0 | `[40, -30, 0]` | 1 |
| 1 | `[40, -75, 0]` | 2 |
| 2 | `[100, -25, 0]` | 3 |
| 3 | `[95, -70, 0]` | 4 |

Default motor IDs are sequential (module 1 = 1–4, module 2 = 5–8, … module 12 = 45–48)
to prevent crashes on load. Motor IDs are always wrong by default and must be overridden
by the operator before running the show. Module count is variable; operator can add or
remove modules.

### GUI layout

Single-page browser app. Three regions:

```
┌─────────────────────────────────────────────────────┐
│  [Place/Edit]  [Aim]     Save    Controller Status  │  ← toolbar
├────────────────────────┬────────────────────────────┤
│                        │  Selected module panel:    │
│   Top-down canvas      │    Name / pos X,Y / yaw   │
│   (drag modules,       │    Cluster list:           │
│    click to select,    │      motor IDs (editable)  │
│    aim-click in        │      pos offsets           │
│    Aim mode)           │    [Test move] per cluster │
│                        │    [Hold at ___°] input    │
└────────────────────────┴────────────────────────────┘
```

**Canvas:** World-space top-down view, same coordinate convention as the visualizer
(X=right, Y=forward → down on screen). 100 cm grid. Each module shown as a labelled dot
with 4 cluster dots and a yaw arrow. Drag module dot to reposition. Drag rotate handle
(small circle on the yaw arrow tip) to set yaw. Click module to select it.

**Toolbar:**
- Mode toggle: **Place/Edit** | **Aim** (explicit, not context-sensitive)
- **Save** button (writes `settings.json`, backs up `.bak`)
- Controller status indicators: `● ONLINE` / `● OFFLINE` per controller, last-checked
  timestamp, **Refresh** button, auto-refresh every 10 s

**Side panel (selected module):**
- Name (text input)
- Registration point X, Y (numeric inputs, cm) — synced bidirectionally with canvas drag
- Yaw (numeric input, degrees) — synced with rotate handle
- Per-cluster: motor ID (numeric input), pos offset X/Y (numeric inputs)
- **Test move** button per cluster — sends `/cg/ff/rot [motor_id, 30]` then
  `/cg/ff/rot [motor_id, 0]` with 500 ms delay; operator watches physical motor
- **Hold at ___°** input + button — sends `/cg/ff/rot [motor_id, deg]` continuously at
  2 Hz until operator clicks Stop or changes mode

### Manual aim (Aim mode)

Requires laptop on show network. Operator selects a cluster in the side panel, switches
to Aim mode, clicks anywhere on the canvas. The tool computes the yaw from the cluster's
world position to the clicked world position and sends `/cg/ff/rot [motor_id, yaw_deg]`
directly to the controller IP from `network.json`. No relay through show computer.

The `--calibrate-yaw` mode is retained (since #254 it is `calibrate_motors.py --yaw`, no longer a `main.py` flag) — it holds **all**
motors at a fixed angle simultaneously, useful for physically aligning flower zero points.

### Controller status

TCP connect to each controller's OSC port (from `network.json`, default 9000), 500 ms
timeout. Reports `ONLINE` / `OFFLINE` per controller. Does not require firmware changes.

*Note, 2026-11-18: built differently. The tool sends `/cg/ff/ping` over OSC and shows the `/cg/ff/pong` reply (`diag.osc_ping`).*

### What is removed

| Item | Action |
|------|--------|
| `ShowControl/FlowerBeds/layout_calibrator.py` | Delete |
| `--layout-calibrate` CLI flag and `run_layout_calibrate_cli()` | Delete from `main.py` |
| `run_layout_calibration()` | Delete from `main.py` |
| `_layout_calibrated_path()`, `apply_layout_overrides()` | Delete from `main.py` |
| `_layout_calibrate_event` and restart loop branch | Delete from `main.py` |
| `/layout-calibrate/start` endpoint | Delete from `visualizer.py` |
| `register_layout_calibrate_callback()` | Delete from `visualizer.py` |
| Layout-calibrate button + JS in visualizer HTML | Delete from `visualizer.py` |
| `layout_calibration` block in `settings.json` | Delete |
| `marker_id` field on modules in `settings.json` | Delete |
| `marker_id: int \| None` field on `ModuleConfig` | Delete from `flower_beds.py` |
| `opencv-python-headless` | Remove from `requirements.txt` |
| ADR-0009 | Status → Superseded |

## Consequences

- No overhead camera, no printed markers, no OpenCV required at setup time.
- `settings.json` is the only layout file; `layout_calibrated.json` no longer exists.
- Layout changes are visible and verifiable before the show starts.
- Motor ID errors are caught early via test-move, not discovered when show fails.
- `opencv-python-headless` removed from production dependencies.
- Laptop must be on the show network to use manual aim / OSC test features.
  Controller status and save work offline (no network needed for file editing).
