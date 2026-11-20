# IIVision

Shared depth-camera computer-vision library. Installed as the `IIVision` package (`pyproject.toml` at the repo root).

- **Public API:** everything exported from `__init__.py`. Import from the package, not from its modules.
- **Coordinates:** `orbbec_to_world()` converts camera space (metres) to world space (centimetres). The axes are in `docs/agents/conventions.md`.

| Module | What it does |
|---|---|
| `camera.py` | `OrbbecCamera` and `MockCamera` (no hardware) |
| `types.py` | Data types: `FramePacket`, `CameraIntrinsics`, `DetectionConfig`, `Blob2D`, `Blob3D`, `DetectionResult` |
| `calibration.py` | Fixed background model: `Calibrator` builds a `Calibration` from N frames |
| `detector.py` | `BlobDetector`: per-frame background subtraction, despeckle, blobs, 3D positions (`BlobTracker` is an alias of the old name) |
| `adaptive_background.py` | Self-learning background (ADR-0023) |
| `blob_stabilizer.py` | Cross-frame IDs and smoothing: `TrackedBlob` |
| `pipeline.py` | `build_calibration()` and `run_pipeline()`: the stages wired together |
| `transforms.py` | `Transform`, `Rotator`, camera-to-world conversion |
| `silhouette_warp.py` | Reprojects a silhouette to a virtual camera (FundingCAPTCHA) |

## How detection works

`BlobDetector`, per frame:

1. **Background subtraction:** a pixel is foreground when it is nearer than the background by more than the model's threshold.
2. **Majority filter, twice:** a 3×3 despeckle.
3. **Connected components:** 8-connected blobs (`scipy.ndimage.label`).
4. **3D position:** pinhole unprojection with the blob's median depth, then camera space to world space.

It reads any background model that has `background`, `valid_mask` and `threshold()`. FlowerBeds uses `Calibration`, a per-pixel median over `calibration_frames` frames. FundingCAPTCHA uses `AdaptiveBackground`, learned continuously: the farthest steady depth wins (ADR-0023).

`BlobStabilizer`, across frames:

- Matches each blob to the nearest existing track within `max_match_dist_cm`.
- Smooths position: `pos = alpha * new + (1 - alpha) * prev`.
- Drops a track missed for more than `max_miss_frames` frames.
- Holds back a new track until it has been seen `min_confirm_frames` frames in a row.

**Used by:** FlowerBeds (the full pipeline) and FundingCAPTCHA (background subtraction, silhouette warp, `BlobStabilizer`).

**Tests:** `test_*.py` here; `uv run pytest IIVision`.
