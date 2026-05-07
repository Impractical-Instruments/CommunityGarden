# Architecture & Pipeline

## Repository layout

```
CommunityGarden/
├── IIVision/                               # Shared computer-vision library
├── ShowControl/
│   ├── FlowerBeds/                         # FlowerBeds Element show control
│   ├── FundingCAPTCHA/                     # FundingCAPTCHA Element show control
│   ├── TreeHouse/                          # TreeHouse Element show control
│   ├── Dashboard/                          # Show-operator browser dashboard (FastAPI)
│   ├── OSCFabric/                          # Shared OSC client for cross-element messaging
│   └── network.json                        # Single source of truth: all IPs, MACs, ports
├── Firmware/
│   ├── FlowerBeds_Follow_ServoController/  # OpenRB-150 Arduino — drives Dynamixel servos
│   ├── TreeHouse_BranchController/         # Branch motor Arduino sketch
│   └── TreeHouse_PicoLEDs/                 # Pico MicroPython LED driver
├── TouchOSC/                               # Layout for manual motor testing
├── docs/
│   ├── adr/                                # Architecture Decision Records
│   └── agents/                             # Agent guidance (this directory)
├── scripts/hooks/                          # smoke_test.py, firmware_config_gen.py
├── Makefile                                # `make test` — runs all tests
├── pytest.ini                              # testpaths = ShowControl IIVision
└── CONTEXT.md                              # Domain glossary — read before naming anything
```

## IIVision — shared CV library

`IIVision/` is a standalone Python package used by FlowerBeds and FundingCAPTCHA.

| Module | Contents |
|---|---|
| `blob_tracker.py` | `BlobTracker`, `Blob2D`, `Blob3D`, `FramePacket` — per-frame detection |
| `blob_stabilizer.py` | `BlobStabilizer`, `StabilizerConfig` — cross-frame tracking + EMA smoothing |
| `camera.py` | `OrbbecCamera`, `MockCamera` — frame iterator abstraction |
| `transforms.py` | `Transform`, `Rotator`, coordinate helpers |
| `pipeline.py` | `run_pipeline`, `build_calibration`, `Calibration` — wires the above together |

Import from the `IIVision` package directly, not from its internal modules.

## OSCFabric — cross-element messaging

`ShowControl/OSCFabric/` wraps `python-osc` and reads addresses from `network.json`. Use `FabricClient` for any outbound OSC that crosses Element boundaries (e.g. FlowerBeds → TreeHouse). The full address schema is in `docs/adr/0007-osc-fabric-schema.md`.

## FlowerBeds pipeline (per frame)

```
OrbbecCamera.frames() / MockCamera.frames()
  → IIVision.run_pipeline()
      → BlobTracker.detect(frame)        # background subtraction + 3D unproject
      → BlobStabilizer.update(blobs)     # greedy nearest-neighbour + EMA smoothing
  → Coordinator.process_tracked_blobs()  # cluster assignment + yaw calculation
  → SimpleUDPClient → Arduino            # OSC /cg/ff/rot [motor_id, rotation_deg]
  → FabricClient → TreeHouse             # OSC /flowerbeds/activity [float 0–1]
  → visualizer.broadcast(state)          # WebSocket → browser dashboard
```

## Blob detection (BlobTracker)

Runs per frame once calibrated:

1. **Background subtraction** — per-pixel depth delta vs median background
2. **Majority filter ×2** — 3×3 neighbourhood despeckle
3. **Connected components** — 8-connected blobs via `scipy.ndimage.label`
4. **3D unproject** — pinhole model, median-Z windowing, camera → world coordinates

Calibration collects `calibration_frames` frames (from `settings.json`) to build a per-pixel median background and validity mask.

## Blob stabilisation (BlobStabilizer)

- Greedy nearest-neighbour matching within `max_match_dist_cm`
- EMA smoothing: `pos = alpha * new + (1 - alpha) * prev`
- Drops tracks missing for more than `max_miss_frames` frames
- Suppresses new tracks until seen for `min_confirm_frames` consecutive frames

## Coordinator → FlowerModule → FlowerCluster

`Coordinator` fans out to `FlowerModule` objects, which fan out to `FlowerCluster` objects. Each frame:

1. `Coordinator.process_tracked_blobs(blobs)` → each module
2. `FlowerModule.update(blobs)` → each cluster
3. `FlowerCluster.update(blobs)` — Attraction policy picks the target Visitor, returns `MotorCommand`

The Attraction policy scores candidates by proximity, dwell time, and inertia. See `CONTEXT.md` for term definitions.

## Visualizer

`visualizer.py` runs a FastAPI WebSocket server (default port 8765). Each frame, `broadcast(state)` pushes a JSON snapshot of blobs, clusters, and camera positions to all connected browser clients. The Show Dashboard (`ShowControl/Dashboard/`) aggregates per-Element visualizers into a single operator view.
