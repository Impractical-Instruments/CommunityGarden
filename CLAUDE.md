# CLAUDE.md — CommunityGarden

AI assistant guide for the **CommunityGarden** codebase — show control software for the interactive flower installation at [Connect Beyond Festival](https://www.connectbeyondfestival.com/).

---

## Project Overview

This is a **Python** show control system that uses computer vision (Orbbec depth camera) to detect people and drive physical flower servo motors in response. The system:

1. Captures depth frames from an Orbbec camera
2. Detects human-presence blobs in 3D space via background-subtraction + connected-component analysis
3. Stabilizes blob tracks across frames using greedy nearest-neighbour matching and EMA smoothing
4. Maps stable blob positions to nearby flower clusters
5. Sends OSC messages over UDP to Arduino motor controllers
6. Arduino controllers drive Dynamixel servos to rotate physical flowers toward detected people

---

## Repository Structure

```
CommunityGarden/
├── ShowControl/
│   └── FlowerBeds/            # Python show-control application
│       ├── main.py            # Entry point and main loop
│       ├── flower_beds.py     # Core logic: Coordinator, FlowerModule, FlowerCluster
│       ├── flower_controller.py  # OSC client for one controller board
│       ├── blob_tracker.py    # Depth-frame blob detection (background subtraction + 3D unproject)
│       ├── blob_stabilizer.py # Cross-frame tracking with EMA smoothing
│       ├── camera.py          # Orbbec camera + MockCamera abstraction
│       ├── transforms.py      # World-space coordinate helpers (Transform, Rotator, etc.)
│       ├── visualizer.py      # FastAPI/WebSocket live top-down debug view
│       ├── settings.json      # Runtime configuration (cameras, modules, controllers)
│       └── requirements.txt   # Python dependencies
├── Firmware/
│   └── FlowerBeds_Follow_ServoController/   # Arduino sketch: receives OSC → drives Dynamixel servos
├── TouchOSC/
│   └── FlowerBedTester.tosc   # TouchOSC layout for manual motor testing
├── .gitattributes
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Primary language | Python 3.11+ |
| Computer vision | Custom numpy/scipy blob tracker (background subtraction + pinhole unproject) |
| Depth camera | Orbbec SDK v2 via `pyorbbecsdk2` |
| Networking | OSC over UDP via `python-osc` |
| Visualizer | FastAPI + WebSocket + embedded browser client (uvicorn) |
| Motor hardware | Dynamixel servos via `Dynamixel2Arduino` library |
| Microcontroller | OpenRB-150 (SAMD21) running Arduino firmware |
| Control UI | TouchOSC layout for manual testing |

---

## Python Code Conventions

### Module Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Argument parsing, config loading, main frame loop, wiring everything together |
| `flower_beds.py` | `Coordinator`, `FlowerModule`, `FlowerCluster` — cluster assignment and yaw calculation |
| `flower_controller.py` | `FlowerController` — wraps `python-osc` UDP client |
| `blob_tracker.py` | `BlobTracker` — stateful per-camera blob detection; `Blob2D`, `Blob3D`, `FramePacket` |
| `blob_stabilizer.py` | `BlobStabilizer` — cross-frame ID assignment and EMA de-jittering |
| `camera.py` | `OrbbecCamera`, `MockCamera` — frame iterator abstraction |
| `transforms.py` | `Transform`, `Rotator`, coordinate conversion helpers |
| `visualizer.py` | FastAPI WebSocket server; `broadcast(state)` called each frame |

### Coordinate System

**World space** (installation frame): **X=right, Y=forward, Z=up, centimetres** — right-handed, matching the Orbbec camera's axis conventions.

**Camera space** (Orbbec native output): **X=right, Y=down, Z=forward, metres**.

`Blob3D.world_pos_cm()` converts from camera space to world space:
- World X ← Camera X (right → right)
- World Y ← Camera Z (forward → forward)
- World Z ← −Camera Y (up = −down)

### Rotation Convention

`Rotator` stores pitch/yaw/roll in degrees:
- **Pitch** — rotation around X (right) axis; positive = nose up
- **Yaw** — rotation around Z (up) axis; positive = rotate from forward toward right
- **Roll** — rotation around Y (forward) axis
- Applied intrinsically in order: Roll → Pitch → Yaw

Yaw of 0° means facing +Y (forward). Yaw of 90° means facing +X (right).

### Logging

Use the named logger throughout:

```python
import logging
log = logging.getLogger("flower_beds")
log.info("...")
log.warning("...")
log.error("...")
```

---

## Architecture & Key Patterns

### Main Loop

`main.py` drives the pipeline each frame:

```
camera.frames()
  → BlobTracker.detect(frame)          # background subtraction + 3D unproject
  → transform_position(camera_transform, blob.world_pos_cm())   # camera → world space
  → BlobStabilizer.update(raw_positions)  # ID assignment + EMA smoothing
  → Coordinator.process_tracked_blobs(tracked_positions)        # cluster assignment
  → FlowerController.send_all(commands)   # OSC → Arduino
  → visualizer.broadcast(state)           # WebSocket → browser
```

### Blob Detection Pipeline

`BlobTracker` (in `blob_tracker.py`) runs per frame once calibrated:

1. **Background subtraction** — per-pixel depth delta vs median background
2. **Majority filter ×2** — 3×3 neighbourhood despeckle
3. **Connected components** — 8-connected blobs via `scipy.ndimage.label`
4. **3D unproject** — pinhole model, median-Z windowing, camera → world coordinate conversion

Calibration collects `N` frames (configurable via `calibration_frames` in `settings.json`) to build a per-pixel median background and validity mask.

### Blob Stabilization

`BlobStabilizer` (in `blob_stabilizer.py`) runs after detection:
- Greedy nearest-neighbour matching within `max_match_dist_cm`
- EMA smoothing: `pos = alpha * new + (1 - alpha) * prev`
- Drops tracks missing for more than `max_miss_frames` frames
- Suppresses new tracks until seen for `min_confirm_frames` consecutive frames

### Coordinator Pattern

`Coordinator` holds a list of `FlowerModule` objects. Each `FlowerModule` holds a list of `FlowerCluster` objects. Each frame:
1. `Coordinator.process_tracked_blobs(blobs)` fans out to all modules
2. `FlowerModule.update(blobs)` fans out to all clusters
3. `FlowerCluster.update(blobs)` finds nearest blob, computes yaw, returns `MotorCommand`

### OSC Communication Flow

```
Python (FlowerController) --UDP/OSC--> Arduino (192.168.1.50:9000)
  address: /cg/ff/rot
  args:    [int motor_id, float rotation_deg]
```

The Arduino firmware listens on `/cg/ff/rot` and calls `setRotDeg()` to drive the target Dynamixel servo.

### Visualizer

`visualizer.py` runs a FastAPI WebSocket server (default port 8765). Each frame, `broadcast(state)` pushes a JSON snapshot of blobs, clusters, and camera positions to all connected browser clients. Open `http://<show-computer-ip>:8765` to see the live top-down view.

---

## Configuration Reference

### settings.json Structure

```json
{
  "calibration_frames": 60,

  "stabilizer": {
    "max_match_dist_cm": 80.0,
    "smoothing_alpha": 0.3,
    "max_miss_frames": 8,
    "min_confirm_frames": 2
  },

  "controllers": [
    { "ip": "192.168.1.50", "port": 9000 }
  ],

  "modules": [
    {
      "registration_point_cm": [100.0, -200.0, 0.0],
      "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
      "clusters": [
        {
          "motor_id": 1,
          "pos_offset_cm": [40.0, 0.0, 0.0],
          "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}
        }
      ]
    }
  ],

  "cameras": [
    {
      "name": "Entrance",
      "pos_cm": [0.0, -300.0, 200.0],
      "rotation": {"pitch": -30.0, "yaw": 0.0, "roll": 0.0},
      "serial": "CPCG853000CB",
      "width": 640,
      "height": 400,
      "framerate": 10
    }
  ]
}
```

- `motor_id` must match the Dynamixel servo ID configured via the `Dynamixel_Config` firmware.
- `serial` must match the serial printed on the Orbbec device. Leave empty to use the first detected camera.
- `registration_point_cm` is the physical anchor of each module in world space (centimetres). X=right, Y=forward, Z=up.
- All position vectors use the world coordinate system: **[X_right, Y_forward, Z_up]** in centimetres.

### Network Setup

- Arduino controller default IP: `192.168.1.50`, port `9000`
- MAC address is hardcoded in firmware: `DE:AD:BE:EF:15:00`
- All devices must be on the same LAN subnet

---

## Running the Show Control

### Prerequisites

- Python 3.11+
- Orbbec SDK v2 (for real camera; not needed in mock mode)

### Install dependencies

```bash
cd ShowControl/FlowerBeds
pip install -r requirements.txt
```

### Run (real hardware)

```bash
python main.py --config settings.json
```

### Run (mock camera, no hardware)

```bash
python main.py --config settings.json --mock-camera --no-osc
```

### Run (headless, no visualizer)

```bash
python main.py --config settings.json --no-visualizer
```

### CLI flags

| Flag | Description |
|---|---|
| `--config PATH` | Path to settings JSON (default: `settings.json`) |
| `--mock-camera` | Use mock camera (random blobs, no hardware required) |
| `--no-osc` | Disable OSC output to Arduino |
| `--no-visualizer` | Disable WebSocket visualizer server |
| `--visualizer-port N` | Visualizer HTTP port (default: 8765) |
| `--verbose` / `-v` | Enable DEBUG logging |

---

## Firmware

Open `.ino` files in Arduino IDE:

- **`FlowerBeds_Follow_ServoController`** — deploy to each OpenRB-150 controller board. Update the `ip` and `mac` variables for each board if running multiple controllers.

Required Arduino libraries:
- `Dynamixel2Arduino`
- `Ethernet`
- `OSCMessage` (CNMAT OSC library)

---

## No Formal Tests or CI

There is currently no automated test suite and no CI/CD pipeline. Verification is done by:
1. Running with `--mock-camera --no-osc` to exercise the full pipeline without hardware
2. Connecting the live visualizer at `http://<show-computer-ip>:8765` to observe blob tracking
3. Using the TouchOSC layout (`TouchOSC/FlowerBedTester.tosc`) for manual motor validation

When making changes, manually verify the full pipeline: camera → blob detection → stabilization → OSC → servo movement.

---

## Git Workflow

- **Main branch:** `main`
- **Feature branches:** use descriptive names (e.g., `claude/update-claude-docs-0DCew`)
- No pre-commit hooks are installed; review changes manually before committing
- Commit messages are informal/descriptive (not conventional commits format)

```bash
git push -u origin <branch-name>
```

---

## Key Things to Know Before Making Changes

1. **OSC address is `/cg/ff/rot`.** `flower_controller.py` and the Arduino firmware (`FlowerBeds_Follow_ServoController.ino`) must agree on this address — change it in both places if needed.
2. **World coordinate system: X=right, Y=forward, Z=up, centimetres.** Camera space (Orbbec native) is X=right, Y=down, Z=forward in metres. `Blob3D.world_pos_cm()` converts between them.
3. **Dynamixel motor IDs must match config.** `ClusterConfig.motor_id` in `settings.json` must match the ID programmed into the servo hardware.
4. **Do not hardcode network addresses, positions, or motor IDs** — they all belong in `settings.json`.
5. **Mock mode** (`--mock-camera`) works without any hardware and is the fastest way to test logic changes.
6. **`pyorbbecsdk2`** is only needed for real camera operation; mock mode runs without it installed.

---

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`Impractical-Instruments/CommunityGarden`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
