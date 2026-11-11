# IIVision

Shared depth-camera computer-vision library. Installed as the `IIVision` package (`pyproject.toml` at the repo root).

- **Public API:** everything exported from `__init__.py`. Import from the package, not from its modules.
- **Coordinates:** camera space is X right, Y down, Z forward, in metres. World space is X right, Y forward, Z up, in centimetres. `orbbec_to_world()` converts; never mix the two.

| Module | What it does |
|---|---|
| `camera.py` | `OrbbecCamera` and `MockCamera` (no hardware) |
| `blob_tracker.py` | Per-frame detection: background subtraction, despeckle, blobs, 3D positions; fixed `Calibration` |
| `adaptive_background.py` | Self-learning background (ADR-0023) |
| `blob_stabilizer.py` | Cross-frame IDs and smoothing: `TrackedBlob` |
| `pipeline.py` | `build_calibration()` and `run_pipeline()`: the stages wired together |
| `transforms.py` | `Transform`, `Rotator`, camera-to-world conversion |
| `silhouette_warp.py` | Reprojects a silhouette to a virtual camera (FundingCAPTCHA) |

**Used by:** FlowerBeds (the full pipeline) and FundingCAPTCHA (background subtraction, silhouette warp, `BlobStabilizer`).

**Tests:** `test_*.py` here; `python -m pytest IIVision`.
