# IIVision

Shared depth-camera computer-vision library. Installed as the `IIVision` package (`pyproject.toml` at the repo root).

- **Public API:** everything exported from `__init__.py`. Import from the package, not from its modules.
- **Coordinates:** camera space is X right, Y down, Z forward, in metres. World space is X right, Y forward, Z up, in centimetres. `orbbec_to_world()` converts; never mix the two.

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

**Used by:** FlowerBeds (the full pipeline) and FundingCAPTCHA (background subtraction, silhouette warp, `BlobStabilizer`).

**Tests:** `test_*.py` here; `uv run pytest IIVision`.
