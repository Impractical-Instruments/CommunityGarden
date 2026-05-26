# FlowerBeds

Servo-driven flowers at the entrance Element. Mirrors at flower centres track Visitors using a depth camera. Theme: surveillance and self-image.

**Host:** `flowerbeds` · 192.168.1.11 · **Visualizer:** http://192.168.1.11:8765 · **Service:** `flowerbeds`

---

## Architecture summary

A depth camera (Orbbec, USB) feeds the IIVision pipeline: background subtraction → blob detection → cross-frame stabilisation (`BlobTracker` with EMA smoothing). Stabilised Blob Tracks are passed to the `Coordinator`, which holds one `FlowerCluster` per servo motor. Each FlowerCluster runs the **Attraction** policy each frame — a weighted sum of proximity, dwell, and inertia — to pick the Visitor it should look at, and produces a `MotorCommand`.

`MotorCommand`s are sent via OSC (`/cg/ff/rot [motor_id, yaw_deg]`) to **OpenRB-150** Dynamixel controllers on the show LAN (`192.168.1.50` / `.51`). The controllers fan out RS-485 to the servos themselves.

FlowerBeds also publishes `/flowerbeds/activity` (float 0–1) onto the OSC Fabric for the TreeHouse Hub.

Key references:
- ADR-0007 — OSC Fabric schema
- ADR-0015 — GUI layout tool (supersedes the ArUco auto-layout ADR-0009)
- `flower_beds.py` — Coordinator, FlowerCluster, Attraction
- `IIVision/` — camera + pipeline

---

## Settings — `settings.json`

Layout — `coordinator.modules[]` — written by the layout tool (next section). Each module has `registration_point_cm`, `rotation` (pitch/yaw/roll), and `clusters[]` (each cluster = one motor, with its own `motor_id`, `pos_offset_cm`, `rotation_offset`, and optional `yaw_limit_deg`).

Attraction tuning — `coordinator.attraction`:
- `influence_radius_cm` — how far a Visitor must be to be considered
- `distance_weight` + `distance_falloff_cm` — proximity score
- `dwell_weight` + `dwell_halflife_frames` — bonus for lingering
- `inertia_weight` — bonus for the previous frame's target (anti-jitter)
- `exclusion_radius_cm` — Visitors closer than this are ignored (anti-self-detection)

Pipeline — `stabilizer` (BlobTracker EMA, match distance, confirm/miss frames), `calibration_frames` (default 60 — the BG model length), `cameras[]` (Orbbec pose: `pos_cm`, `rotation`, `width/height/framerate`), `activity_max_blobs` (normaliser for `/flowerbeds/activity`).

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
- `--network <path>` — default `../../network.json` (the show-network file)
- `--port N` — default 8764
- `--no-browser` — don't open browser

Features:
- Drag-place modules on a top-down canvas. Rotate handle or numeric input for yaw.
- Per-cluster motor ID editing (defaults are sequential placeholders — always override).
- Per-cluster `yaw_limit_deg` (default 60°) — caps cluster local yaw, applied by the coordinator at runtime.
- **Manual aim** — click on canvas → POST `/api/aim` → server sends `/cg/ff/rot [motor_id, -deg]` to every controller IP from `network.json`. (`deg` is negated: software CCW+ → OSC CW+.)
- **Test move** per cluster — fires a short sequence to confirm a specific motor responds.
- **Controller status** — TCP-ping each `flowerbeds_controller_*` every 10 s; on success surfaces baud, scanned servo IDs, rx/drop counters.

Aim and controller-status features need the laptop on the show LAN. Save and offline editing work without.

After saving, restart the show:

```bash
ssh flowerbeds "sudo systemctl restart flowerbeds"
```

---

## `main.py` flags

| Flag | Effect |
|---|---|
| `--config <path>` | Settings file (default `settings.json`) |
| `--mock-camera` | Synthetic blob stream (no Orbbec) |
| `--no-osc` | Don't send motor commands or OSC Fabric reports |
| `--no-visualizer` | Disable WebSocket visualizer server |
| `--visualizer-port N` | Default 8765 |
| `--recalibrate` | Ignore saved `.calibration.npz`, rebuild background model |
| `--verbose` / `-v` | DEBUG logging |
| `--calibrate-yaw DEG` | Calibration mode: hold every motor at this yaw (deg), no camera. 0=forward, 90=right, -90=left. Crew physically rotates flowers to a known reference. |
| `--calibrate-yaw-sweep` | Sweep mode: cycle every motor through `-yaw_limit, 0, +yaw_limit, 0`. Crew verifies cluster cones match physical travel. Uses each cluster's own `yaw_limit_deg`. |
| `--sweep-period-s SECS` | Sweep cycle period (default 4.0) |

---

## OSC interface

| Address | Direction | Args | Notes |
|---|---|---|---|
| `/cg/ff/rot` | out (to controllers) | `[motor_id:int, yaw_deg:float]` | Per-motor command, sent every frame to **every** configured controller (controllers ignore IDs they don't own) |
| `/cg/ff/ping` | out | — | Boot-time diagnostic (`diag.py`) |
| `/cg/ff/pong` | in | (controller status) | Reports scanned servo IDs + rx/drop counters |
| `/flowerbeds/activity` | out (Fabric) | `float 0–1` | `min(1, len(tracked)/activity_max_blobs)`, every frame |
| `/flowerbeds/mode` | in (Fabric) | `string` | `active` / `dim` / `inactive` — relayed by Dashboard |

---

## Boot diagnostics

On start (after calibration loads), `main.py` pings every controller and logs:

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
| Flower aims past max travel | Cluster `yaw_limit_deg` larger than physical cone | Tighten in layout tool, run `--calibrate-yaw-sweep` to verify |
| Visualizer empty | Camera background not yet built | Wait ~60 frames; check `calibration_state` field in WebSocket payload |
