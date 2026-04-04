# CLAUDE.md — CommunityGarden

AI assistant guide for the **CommunityGarden** codebase — show control software for the interactive installations at [Connect Beyond Festival](https://www.connectbeyondfestival.com/).

---

## Project Overview

This repo contains two show-control systems sharing the same Orbbec depth camera hardware:

### 1. FlowerBeds
A Python system that detects people via computer vision and rotates physical flower servo motors toward them:
1. Captures depth frames from an Orbbec camera
2. Detects human-presence blobs via background subtraction + connected-component analysis
3. Stabilizes blob tracks across frames (greedy nearest-neighbour matching + EMA smoothing)
4. Maps stable blob positions to nearby flower clusters
5. Sends OSC messages over UDP to Arduino motor controllers
6. Arduino controllers drive Dynamixel servos to rotate physical flowers toward detected people

### 2. FundingCAPTCHA
A Godot 4.6 game projected onto a physical surface where players solve increasingly surreal CAPTCHAs by touching cells on the projected screen. A Python touch-detection process uses a projector-mounted Orbbec camera to detect finger contacts and report grid-cell events to Godot over OSC.

---

## Repository Structure

```
CommunityGarden/
├── ShowControl/
│   ├── FlowerBeds/                    # Python show-control for the flower installation
│   │   ├── main.py                    # Entry point and main loop
│   │   ├── flower_beds.py             # Coordinator, FlowerModule, FlowerCluster
│   │   ├── flower_controller.py       # OSC client for one controller board
│   │   ├── blob_tracker.py            # Depth-frame blob detection (background subtraction + 3D unproject)
│   │   ├── blob_stabilizer.py         # Cross-frame tracking with EMA smoothing
│   │   ├── camera.py                  # OrbbecCamera + MockCamera abstraction
│   │   ├── transforms.py              # UE-style coordinate math
│   │   ├── visualizer.py              # FastAPI/WebSocket live top-down debug view
│   │   ├── settings.json              # Runtime configuration
│   │   └── requirements.txt
│   └── FundingCAPTCHA/
│       ├── funding-captcha/           # Godot 4.6 game project
│       │   └── project.godot
│       └── TouchScreen/               # Python touch-detection process
│           ├── main.py                # Entry point and state machine
│           ├── touch_detector.py      # Background calibration + per-frame touch blob detection
│           ├── calibration.py         # 4-corner homography (camera px → screen UV), save/load
│           ├── touch_tracker.py       # Grid cell debounce → DOWN/UP events
│           ├── camera.py              # OrbbecCamera + MockCamera (self-contained)
│           ├── visualizer.py          # FastAPI/WebSocket dual-panel debug view
│           ├── settings.json          # Runtime configuration
│           └── requirements.txt
├── Firmware/
│   └── FlowerBeds_Follow_ServoController/   # Arduino: receives OSC → drives Dynamixel servos
├── TouchOSC/
│   └── FlowerBedTester.tosc           # TouchOSC layout for manual motor testing
├── .gitattributes
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Primary language | Python 3.11+ |
| Game engine | Godot 4.6 (FundingCAPTCHA) |
| Computer vision | Custom numpy/scipy (background subtraction + pinhole unproject) |
| Depth camera | Orbbec SDK v2 via `pyorbbecsdk2` |
| Networking | OSC over UDP via `python-osc` |
| Visualizer | FastAPI + WebSocket + embedded browser client (uvicorn) |
| Motor hardware | Dynamixel servos via `Dynamixel2Arduino` library |
| Microcontroller | OpenRB-150 (SAMD21) running Arduino firmware |
| Control UI | TouchOSC layout for manual testing |

---

## FlowerBeds — Python Show Control

### Module Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Argument parsing, config loading, main frame loop, wiring |
| `flower_beds.py` | `Coordinator`, `FlowerModule`, `FlowerCluster` — cluster assignment and yaw calculation |
| `flower_controller.py` | `FlowerController` — wraps `python-osc` UDP client |
| `blob_tracker.py` | `BlobTracker` — stateful per-camera blob detection; `Blob2D`, `Blob3D`, `FramePacket` |
| `blob_stabilizer.py` | `BlobStabilizer` — cross-frame ID assignment and EMA de-jittering |
| `camera.py` | `OrbbecCamera`, `MockCamera` — frame iterator abstraction |
| `transforms.py` | `UETransform`, `UERotator`, coordinate conversion helpers |
| `visualizer.py` | FastAPI WebSocket server; `broadcast(state)` called each frame |

### Coordinate System

All world positions use UE-style coordinates: **X=forward, Y=right, Z=up, centimetres**.

Camera-space coordinates (from the depth sensor) use: **X=right, Y=down, Z=forward, metres**.

`Blob3D.world_pos_cm()` handles the conversion between these spaces.

### Main Loop Pipeline

```
camera.frames()
  → BlobTracker.detect(frame)               # background subtraction + 3D unproject
  → transform_position(cam_transform, ...)  # camera → world space
  → BlobStabilizer.update(raw_positions)    # ID assignment + EMA smoothing
  → Coordinator.process_world_positions()   # cluster assignment → MotorCommands
  → FlowerController.send_all(commands)     # OSC → Arduino
  → visualizer.broadcast(state)             # WebSocket → browser
```

### Blob Detection Pipeline

`BlobTracker` runs per frame once calibrated:
1. **Background subtraction** — per-pixel depth delta vs median background
2. **Majority filter ×2** — 3×3 neighbourhood despeckle
3. **Connected components** — 8-connected blobs via `scipy.ndimage.label`
4. **3D unproject** — pinhole model, median-Z windowing, camera → UE coordinate conversion

### Blob Stabilization

`BlobStabilizer` runs after detection:
- Greedy nearest-neighbour matching within `max_match_dist_cm`
- EMA smoothing: `pos = alpha * new + (1 - alpha) * prev`
- Drops tracks missing for more than `max_miss_frames` frames
- Suppresses new tracks until seen for `min_confirm_frames` consecutive frames

### OSC Communication

```
Python (FlowerController) --UDP/OSC--> Arduino (192.168.1.50:9000)
  address: /cg/ff/rot
  args:    [int motor_id, float rotation_deg]
```

### FlowerBeds settings.json

```json
{
  "calibration_frames": 60,
  "stabilizer": {
    "max_match_dist_cm": 80.0,
    "smoothing_alpha": 0.3,
    "max_miss_frames": 8,
    "min_confirm_frames": 2
  },
  "controllers": [{ "ip": "192.168.1.50", "port": 9000 }],
  "modules": [{
    "registration_point_cm": [-200.0, 100.0, 0.0],
    "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
    "clusters": [{
      "motor_id": 1,
      "pos_offset_cm": [0.0, 40.0, 0.0],
      "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}
    }]
  }],
  "cameras": [{
    "name": "Entrance",
    "pos_cm": [-300.0, 0.0, 200.0],
    "rotation": {"pitch": -30.0, "yaw": 0.0, "roll": 0.0},
    "serial": "CPCG853000CB",
    "width": 640, "height": 400, "framerate": 10
  }]
}
```

### Running FlowerBeds

```bash
cd ShowControl/FlowerBeds
pip install -r requirements.txt

# Real hardware
python main.py --config settings.json

# Mock camera, no hardware
python main.py --mock --no-osc

# Headless
python main.py --no-visualizer
```

| Flag | Description |
|---|---|
| `--mock` | Mock camera (no hardware required) |
| `--no-osc` | Disable OSC output to Arduino |
| `--no-visualizer` | Disable WebSocket visualizer |
| `--visualizer-port N` | Visualizer HTTP port (default: 8765) |
| `--verbose` / `-v` | Enable DEBUG logging |

Visualizer: `http://<show-computer-ip>:8765`

---

## FundingCAPTCHA — Touch Screen

### Architecture

The camera is mounted to the projector and points at the projected surface. The touch detector uses the same background-subtraction approach as FlowerBeds, but works entirely in 2D pixel space (no 3D unprojection needed for a flat surface).

A one-time 4-corner calibration establishes a homography from camera pixels to screen UV [0,1]², persisted to `calibration.json`.

### Module Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | State machine (background cal → corner cal → running), OSC I/O, main loop |
| `touch_detector.py` | Background calibration + per-frame touch-blob detection → `TouchPoint` list |
| `calibration.py` | `ScreenCalibration` — 4-corner homography, save/load JSON, `to_uv()` mapping |
| `touch_tracker.py` | `GridTouchTracker` — debounces raw detections into `DOWN`/`UP` events per grid cell |
| `camera.py` | `OrbbecCamera` + `MockCamera` — self-contained (no dependency on FlowerBeds) |
| `visualizer.py` | FastAPI WebSocket server; dual-panel canvas (camera view + screen grid) |

### State Machine

```
BACKGROUND_CALIBRATION  →  CORNER_CALIBRATION  →  RUNNING
     (auto, N frames)        (4 user touches)
```

If `calibration.json` exists and `--recalibrate` is not passed, corner calibration is skipped.

### Corner Calibration Flow

1. Python sends `/captcha/cal/prompt idx uv_x uv_y` → Godot projects a dot at that UV position
2. User touches each of the 4 screen corners in sequence
3. Touch detector records the camera pixel centroid for each corner
4. Homography is computed and saved to `calibration.json`
5. Python sends `/captcha/cal/done` → Godot starts the game

### OSC Protocol

| Direction | Address | Args | Meaning |
|---|---|---|---|
| Python → Godot | `/captcha/touch/down` | `col row` | Cell first touched |
| Python → Godot | `/captcha/touch/up` | `col row` | Cell released |
| Python → Godot | `/captcha/state` | `cols rows c0 c1 …` | Full grid state every frame |
| Python → Godot | `/captcha/cal/prompt` | `idx uv_x uv_y` | Show calibration marker at this UV |
| Python → Godot | `/captcha/cal/ack` | `idx` | Corner recorded |
| Python → Godot | `/captcha/cal/done` | — | Calibration complete, start game |
| Godot → Python | `/captcha/grid_size` | `cols rows` | Update active grid dimensions |
| Godot → Python | `/captcha/recalibrate` | — | Restart corner calibration |

Default ports: Python listens on `9002`, sends to `9001` (both localhost).

### TouchScreen settings.json

```json
{
  "camera": { "serial": "", "width": 640, "height": 400, "framerate": 30 },
  "calibration": { "background_frames": 90, "calibration_file": "calibration.json", "corner_inset": 0.05 },
  "detection": { "touch_threshold_mm": 25, "min_touch_pixels": 30, "max_touch_pixels": 8000 },
  "tracker": { "confirm_frames": 3, "release_frames": 8 },
  "grid": { "cols": 4, "rows": 4 },
  "osc": { "target_ip": "127.0.0.1", "target_port": 9001, "listen_port": 9002 }
}
```

- `touch_threshold_mm`: how much closer than background a pixel must be to register as a touch (start low, tune upward if false positives appear)
- `corner_inset`: fraction Godot insets calibration markers from the screen edge — **must match the value used in the Godot calibration scene**
- `confirm_frames` / `release_frames`: debounce. Increase if touches are flickery, decrease for faster response.

### Running TouchScreen

```bash
cd ShowControl/FundingCAPTCHA/TouchScreen
pip install -r requirements.txt

# Real hardware (first run — forces corner calibration)
python main.py --recalibrate

# Real hardware (subsequent runs — loads saved calibration)
python main.py

# Mock camera, no hardware
python main.py --mock --no-osc

# Headless
python main.py --no-visualizer
```

| Flag | Description |
|---|---|
| `--mock` | Mock camera (no hardware required) |
| `--recalibrate` | Force re-run corner calibration even if `calibration.json` exists |
| `--no-osc` | Disable OSC output/input |
| `--no-visualizer` | Disable WebSocket visualizer |
| `--visualizer-port N` | Visualizer HTTP port (default: 8766) |
| `--verbose` / `-v` | Enable DEBUG logging |

Visualizer: `http://<show-computer-ip>:8766`

---

## Firmware

Open `.ino` files in Arduino IDE:

- **`FlowerBeds_Follow_ServoController`** — deploy to each OpenRB-150 controller board. Update the `ip` and `mac` variables for each board if running multiple controllers.

Required Arduino libraries: `Dynamixel2Arduino`, `Ethernet`, `OSCMessage` (CNMAT OSC library)

---

## No Formal Tests or CI

Verification is done manually:

**FlowerBeds:** `python main.py --mock --no-osc` → observe blob tracking in the visualizer at port 8765 → use TouchOSC layout for motor validation.

**TouchScreen:** `python main.py --mock --no-osc` → observe raw touch blobs (camera panel) and grid cells (screen panel) in the visualizer at port 8766.

---

## Git Workflow

- **Main branch:** `main`
- **Feature branches:** use descriptive names
- No pre-commit hooks; review changes manually before committing
- Commit messages are informal/descriptive (not conventional commits format)

---

## Key Things to Know Before Making Changes

### FlowerBeds
1. **OSC address is `/cg/ff/rot`.** `flower_controller.py` and `FlowerBeds_Follow_ServoController.ino` must agree — change both if needed.
2. **Coordinate system is UE-style.** World = X=forward, Y=right, Z=up, cm. Camera = X=right, Y=down, Z=forward, m. `Blob3D.world_pos_cm()` converts.
3. **Dynamixel motor IDs must match config.** `ClusterConfig.motor_id` in `settings.json` must match the hardware-programmed servo ID.

### FundingCAPTCHA TouchScreen
4. **`calibration.json` is machine-specific** — it encodes the exact camera-to-projector geometry for a given physical setup. Do not commit it; regenerate on-site with `--recalibrate`.
5. **`corner_inset` must match Godot.** The Python `corner_inset` setting and the UV positions Godot uses for its calibration marker dots must be identical, or the homography will be wrong.
6. **Touch threshold tuning.** `touch_threshold_mm=25` is conservative. If the screen surface has relief or warps, you may need to increase it. If touches aren't registering, decrease it.
7. **Grid size is runtime-configurable.** Godot sends `/captcha/grid_size cols rows` to change the grid; Python updates immediately without restart.

### Both systems
8. **Do not hardcode network addresses, positions, or IDs** — they all belong in `settings.json`.
9. **`pyorbbecsdk2`** is only needed for real camera operation; mock mode runs without it.
10. **Both systems share the same Orbbec camera hardware** — they cannot run simultaneously on the same machine without hardware multiplexing.
