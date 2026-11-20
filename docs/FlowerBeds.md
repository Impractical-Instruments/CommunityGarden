# FlowerBeds

Servo-driven flowers at the entrance Element. Mirrors at flower centres track Visitors using a depth camera. Theme: surveillance and self-image.

**Host:** `flowerbeds` · 192.168.1.11 · **Visualizer:** http://192.168.1.11:8765 · **Service:** `flowerbeds`

---

## Architecture summary

A depth camera (Orbbec, USB) feeds the IIVision pipeline: background subtraction → blob detection → cross-frame stabilisation (`BlobStabilizer` with EMA smoothing). Stabilised Blob Tracks are passed to the `Coordinator`, which holds one `FlowerModule` per physical module and, inside each, one `FlowerCluster` per servo motor. Each FlowerCluster runs the **Attraction** policy each frame — a weighted sum of proximity, dwell, and inertia — to pick the Visitor it should look at, and produces a `MotorCommand`.

Per frame, in `main.py`:

```
OrbbecCamera / MockCamera
  → IIVision.run_pipeline()               BlobDetector, then BlobStabilizer: TrackedBlobs in world cm
  → Coordinator.process_tracked_blobs()   each FlowerCluster picks a Visitor: MotorCommands
  → ControllerBus.send()                  /cg/ff/rot to every servo controller
  → FabricClient.report("activity", …)    /flowerbeds/activity to the TreeHouse
  → visualizer.broadcast(state)           state snapshot to the browser
```

`MotorCommand`s go by OSC to the **OpenRB-150** Dynamixel controllers on the show LAN (the `flowerbeds_controller_*` entries in `network.json`). The controllers fan out to the servos themselves.

Files in `ShowControl/FlowerBeds/`:

| File | What it holds |
|---|---|
| `main.py` | Argument parsing and the show loop: camera, pipeline, Coordinator, controllers, Fabric, visualizer |
| `flower_beds.py` | `Coordinator`, `FlowerModule`, `FlowerCluster`, `MotorCommand`: which Visitor each cluster looks at, and the yaw to get there |
| `config.py` | The shapes of `settings.json`: `Attraction` (with its scoring formula), `ClusterConfig`, `ModuleConfig`, `CoordinatorConfig`, `CameraConfig` |
| `controllers.py` | `OSC_ROT_ADDRESS`, controller discovery from `network.json`, `ControllerBus` (send, diagnose). The one place the yaw sign flips |
| `diag.py` | `osc_ping()`: `/cg/ff/ping` to one controller, parsed `/cg/ff/pong` back |
| `calibrate_motors.py` | Hold and sweep motor calibration, no camera |
| `layout_tool.py`, `layout_tool/` | Browser GUI for placing modules and aiming clusters (ADR-0015) |
| `visualizer.py`, `state.py` | The live top-down view on a `ShowWeb.LiveServer` (page in `visualizer_static/`), and the per-frame state it shows |
| `stop_signal.py` | `StopSignal`: Ctrl+C and SIGTERM end the loop cleanly |

Camera, blob detection and stabilisation are in `IIVision/` (its README has the modules).

---

## Settings — `settings.json`

Layout — `coordinator.modules[]` — written by the layout tool (next section); do not edit positions by hand. Each module has `name`, `registration_point_cm`, `rotation` (pitch/yaw/roll), and `clusters[]`. Each cluster is one motor, with:
- `motor_id` — required; must match the ID set on the Dynamixel servo. The layout tool's defaults are sequential placeholders
- `pos_offset_cm`, `rotation_offset` — relative to the module
- `yaw_limit_deg` — optional, default 60. The motor command is clamped to ± this, in the cluster's own frame

All positions are world space: X right, Y forward, Z up, in centimetres.

Attraction tuning — `coordinator.attraction`:
- `influence_radius_cm` — Visitors farther than this are not considered
- `distance_weight` + `distance_falloff_cm` — proximity score
- `dwell_weight` + `dwell_halflife_frames` — bonus for lingering
- `inertia_weight` — bonus for the previous frame's target (anti-jitter)

`coordinator.exclusion_radius_cm` — a blob closer than this to any cluster is dropped before tracking, so the flowers do not follow themselves.

Pipeline:
- `stabilizer` — `max_match_dist_cm`, `smoothing_alpha` (EMA), `max_miss_frames`, `min_confirm_frames`
- `calibration_frames` — frames used to build the background model (default 60)
- `cameras[]` — only the first entry is used: `pos_cm`, `rotation`, `width`, `height`, `framerate`, `mirror`. There is no serial-number key; the first Orbbec found is opened
- `activity_max_blobs` — the Visitor count that reports `/flowerbeds/activity` as 1.0 (default 10)

Persisted background calibration: `settings.calibration.npz` (path = `<settings>.calibration.npz`). Loaded on start unless `--recalibrate` or missing/corrupt.

---

## Layout tool

Run on the **operator laptop** (Windows). Visual placement of modules + per-cluster motor verification. Browser GUI; no need to stop the on-host service.

```powershell
cd ShowControl\FlowerBeds
python layout_tool.py
# http://localhost:8764 (auto-opens)
```

Reads/writes only `coordinator.modules[]` in `settings.json`. Backs up `settings.json.bak` on every save.

Flags:
- `--config <path>` — default `settings.json` in cwd
- `--network <path>` — default `ShowControl/network.json`
- `--port N` — default 8764
- `--no-browser` — don't open browser

Features:
- Drag-place modules on a top-down canvas. Rotate handle or numeric input for yaw.
- Per-cluster motor ID editing (defaults are sequential placeholders — always override).
- Per-cluster `yaw_limit_deg` (default 60°) — caps cluster local yaw, applied by the coordinator at runtime.
- **Manual aim** — click on canvas → POST `/api/aim` → server sends `/cg/ff/rot [motor_id, -deg]` to every controller IP from `network.json`. (`deg` is negated: software CCW+ → OSC CW+.)
- **Test move** per cluster — sends 30°, then 0° half a second later, to confirm a specific motor responds. **Hold** re-sends a chosen angle every half second until stopped.
- **Controller status** — sends `/cg/ff/ping` to each `flowerbeds_controller_*` every 10 s; on a reply shows baud, scanned servo IDs, rx/drop counters.

Aim and controller-status features need the laptop on the show LAN. Save and offline editing work without.

After saving, restart the show:

```bash
ssh flowerbeds "sudo systemctl restart flowerbeds"
```

---

## Running `main.py`

The service runs `python3 main.py --config settings.json` from `ShowControl/FlowerBeds`. On a dev machine:

```bash
cd ShowControl/FlowerBeds
uv run python main.py --mock-camera --no-osc      # no hardware: the fastest way to test a logic change
uv run --extra camera python main.py              # real camera and controllers; the Orbbec SDK is the `camera` extra
```

| Flag | Effect |
|---|---|
| `--config <path>` | Settings file (default `settings.json`) |
| `--mock-camera` | Synthetic blob stream (no Orbbec) |
| `--no-osc` | Don't send motor commands or OSC Fabric reports |
| `--no-visualizer` | Disable the visualizer server |
| `--visualizer-port N` | Default 8765 |
| `--recalibrate` | Ignore saved `.calibration.npz`, rebuild background model |
| `--verbose` / `-v` | DEBUG logging |

After a change to the pipeline or the Coordinator:

1. Run with `--mock-camera --no-osc` and confirm the log is clean.
2. Open `http://localhost:8765` and check that blobs, clusters and the camera draw where they should.
3. If the change touches OSC or servo logic, connect real hardware and check with the layout tool's manual aim (one servo at a time) or `calibrate_motors.py --sweep` (every servo through its limits). No test covers the hardware.

---

## Calibrating motors — `calibrate_motors.py`

No camera. Run it with the `flowerbeds` service stopped, or both will command the motors.

```bash
cd ShowControl/FlowerBeds
python3 calibrate_motors.py --yaw 0      # hold every motor at 0° so crew can set each flower to its reference
python3 calibrate_motors.py --sweep      # every motor through -limit, 0, +limit, 0
```

| Flag | Effect |
|---|---|
| `--yaw DEG` | Hold every motor at this yaw (deg) until Ctrl+C. 0=forward, 90=right, -90=left. Crew physically rotates flowers to a known reference. |
| `--sweep` | Cycle every motor through `-yaw_limit, 0, +yaw_limit, 0`. Crew verifies cluster cones match physical travel. Uses each cluster's own `yaw_limit_deg`. |
| `--sweep-period-s SECS` | Sweep cycle period (default 4.0) |
| `--config <path>`, `--no-osc`, `-v` | As for `main.py` |

One of `--yaw` or `--sweep` is required.

---

## OSC interface

FlowerBeds sends `/cg/ff/rot` and `/cg/ff/ping` to its servo controllers, reads `/cg/ff/pong` back, and reports `/flowerbeds/activity` to the TreeHouse when the value changes and on a heartbeat, not every frame. It receives nothing else. Arguments and the send rule: [`osc-fabric.md`](osc-fabric.md).

---

## Boot diagnostics

On start (after calibration loads), `main.py` pings every controller (`ControllerBus.diagnose`) and logs:

```
ctrl flowerbeds_controller_1 (192.168.1.50) — baud=1000000, 28 servo(s): [...] | rx=12345 drop=0
ctrl flowerbeds_controller_2 (192.168.1.51) — baud=1000000, 28 servo(s): [...] | rx=12340 drop=2
Configured motor IDs not found on any controller: [42] (these flowers will NOT move)
```

If a motor ID is in the "not found" line, that flower will not move — even though no error is thrown. First place to check when a flower stops responding.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| All flowers still | OpenRB-150 boards missed switch at boot ([#56](https://github.com/Impractical-Instruments/CommunityGarden/issues/56)) | Confirm switch came up first, power-cycle controllers |
| One flower still | Motor ID in "not found" diagnostic | Verify motor wiring on the controller bus; check `motor_id` in `settings.json` |
| Camera fails to open | Orbbec udev rule missing | See [bootstrap.md → FlowerBeds host](bootstrap.md#flowerbeds-host) |
| Flowers jittery | `inertia_weight` too low | Raise it; watch the visualizer |
| Flowers slow to commit to a Visitor | `dwell_halflife_frames` too high | Lower it |
| Flower aims past max travel | Cluster `yaw_limit_deg` larger than physical cone | Tighten in layout tool, run `calibrate_motors.py --sweep` to verify |
| Visualizer empty | Camera background not yet built | The visualizer gets no state until calibration finishes; wait ~60 frames for `Calibration saved` (or `Loaded calibration`) in the log |
