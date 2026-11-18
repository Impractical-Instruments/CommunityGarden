# Architecture & Pipeline

The directory tree is in [the repo map](../repo-map.md). The shared vision library's modules are in [`IIVision/README.md`](../../IIVision/README.md).

## OSCFabric — cross-element messaging

`ShowControl/OSCFabric/` wraps `python-osc` and reads addresses from `network.json`. Use `FabricClient` for any outbound OSC that crosses Element boundaries (e.g. FlowerBeds → TreeHouse). Every address is in [`docs/osc-fabric.md`](../osc-fabric.md).

## FlowerBeds pipeline (per frame)

```
OrbbecCamera.frames() / MockCamera.frames()
  → IIVision.run_pipeline()
      → BlobDetector.detect(frame)       # background subtraction + 3D unproject
      → BlobStabilizer.update(blobs)     # greedy nearest-neighbour + EMA smoothing
  → Coordinator.process_tracked_blobs()  # cluster assignment + yaw calculation
  → SimpleUDPClient → Arduino            # OSC /cg/ff/rot [motor_id, rotation_deg]
  → FabricClient → TreeHouse             # OSC /flowerbeds/activity [float 0–1]
  → visualizer.broadcast(state)          # WebSocket → browser dashboard
```

## FlowerBeds layout tool

`ShowControl/FlowerBeds/layout_tool.py` — run on the operator's Windows laptop before
show to configure module positions. Not used on the show Pi.

```
python layout_tool.py   →  http://localhost:8764
```

Reads and writes `coordinator.modules[]` in `settings.json` (all other fields preserved).
Backs up `settings.json.bak` before any write. Reads controller IPs from `network.json`.

Key features:
- Drag-place modules on a top-down canvas; set yaw via rotate handle or numeric input
- Per-cluster motor ID editing; default offsets match standard 4-cluster hardware layout
- Manual aim: click canvas point → sends `/cg/ff/rot` directly to controller via OSC
- Test move: sends a 30°→0° command to a single motor to confirm it responds
- Controller status: TCP-ping each controller, auto-refreshes every 10 s

See ADR-0015 for full design and implementation plan.

## Blob detection (BlobDetector)

Runs per frame once calibrated:

1. **Background subtraction** — per-pixel depth delta vs median background
2. **Majority filter ×2** — 3×3 neighbourhood despeckle
3. **Connected components** — 8-connected blobs via `scipy.ndimage.label`
4. **3D unproject** — pinhole model, median-Z windowing, camera → world coordinates

`BlobDetector` reads any background model with `background`, `valid_mask` and `threshold()`. FlowerBeds uses `Calibration`: `Calibrator` collects `calibration_frames` frames (from `settings.json`) to build a per-pixel median background and validity mask. FundingCAPTCHA uses `AdaptiveBackground` (`adaptive_background.py`, ADR-0023), learned continuously from the first frame — the farthest steady depth wins.

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

`visualizer.py` serves the page `visualizer_static/index.html` and a state socket on a `ShowWeb.LiveServer` (default port 8765; the server plumbing, `/ws` and `/logs` live in `ShowControl/ShowWeb/live.py`, shared with the TreeHouse visualizer). Each frame, `broadcast(state)` pushes a JSON snapshot of blobs, clusters, and camera positions to all connected browser clients. The Show Dashboard (`ShowControl/Dashboard/`) aggregates per-Element visualizers into a single operator view.
