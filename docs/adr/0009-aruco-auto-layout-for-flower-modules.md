# ADR 0009 — ArUco auto-layout for Flower Bed modules

**Status:** Superseded by [ADR-0015](0015-flowerbeds-gui-layout-tool.md)

## Context

The FlowerBeds installation has 12 flower modules, each with 4 servo clusters. Their world-space positions and orientations are configured manually in `settings.json` (`registration_point_cm`, `rotation.yaw`). At festival setup, modules are placed roughly in position and then precisely measured and typed into config — a slow, error-prone process. Last-minute repositioning (a common reality at festival installs) requires re-measuring and re-editing the file.

The Orbbec depth camera already has a usable color sensor. The camera is mounted overhead looking straight down, giving a clean top-down view of the floor.

## Decision

Add an ArUco-marker-based layout calibration system. A printed marker placed flat at each module's registration point is detected by the overhead camera; the detected pose (position + yaw) is written to a separate `layout_calibrated.json` file that overrides only the spatial fields at runtime.

**Marker format:** DICT_4X4_50, 40 cm square. This size subtends ~46 px at 4 m overhead in a 640 px-wide frame — enough for reliable detection with margin.

**Pose estimation:** `cv2.solvePnP` with `SOLVEPNP_IPPE_SQUARE` gives full 6-DOF pose from the four tag corners. Position is converted from Orbbec camera space to world space using the existing `orbbec_to_world` + `transform_position` pipeline. Yaw is extracted from the tag's +Y axis projected onto the world XY plane. The tag's +Y axis (top edge when the ID is readable) is defined as the module's forward direction.

**Averaging:** 30 frames (configurable via `layout_calibration.frames` in `settings.json`) are accumulated and averaged — position by arithmetic mean, yaw by circular mean — to smooth out single-frame detection noise.

**Override file pattern:** `settings.json` stores manual/default values and remains versioned. `layout_calibrated.json` (gitignored) is written by calibration and loaded automatically at startup. It is sparse: only `registration_point_cm` and `rotation.yaw` per detected module. Deleting the file reverts to manual values.

**Trigger points:**
- `python main.py --layout-calibrate` — dedicated CLI pass, writes file, exits
- `POST /layout-calibrate/start` on the visualizer server — pauses the show pipeline (~3 s), runs calibration, resumes with updated coordinator

**Mock mode:** Returns an error and exits. Layout calibration requires real camera hardware.

**Partial results:** If a marker is not detected, a warning is logged and that module keeps its existing position. The file is still written with the modules that were found.

## Consequences

- Repositioning 12 modules goes from ~20 minutes of measuring and typing to ~3 minutes of placing tags and pressing a button.
- `settings.json` remains the authoritative manual backup; `layout_calibrated.json` can be deleted to restore it instantly.
- The Orbbec color stream is only opened during calibration (a separate `OrbbecRGBCamera` context); the depth stream is unaffected during normal show operation.
- `opencv-python` is added as a required dependency.
- The `marker_id` field must be set in each module's `settings.json` entry and must match the printed tag ID. Mismatch means the module is silently skipped (it has no `marker_id` to look up).
- Tags must be removed before the show starts — they are not detected during normal operation, but a stray tag on the floor could theoretically be confused for a person blob by the depth tracker.
