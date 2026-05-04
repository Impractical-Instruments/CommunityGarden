"""
ArUco-based layout calibrator for Flower Beds.

Detects ArUco (DICT_4X4_50) markers in RGB frames and computes world-space
positions and yaw angles for each module's registration point.

Orientation convention:
  The tag's +Y axis (upward edge when the ID is readable face-on) maps to the
  module's forward direction (+Y world, yaw=0).  Point the top of the printed
  tag toward where you want the module's flowers to face at rest.

CLI usage:
  python main.py --config settings.json --layout-calibrate

Dashboard usage:
  POST http://<show-ip>:8765/layout-calibrate/start
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from IIVision.transforms import Transform, rotator_to_matrix

log = logging.getLogger("flower_beds")

_ARUCO_DICT_ID = cv2.aruco.DICT_4X4_50

# ArUco marker corner order (OpenCV convention, tag local coords, metres):
#   top-left, top-right, bottom-right, bottom-left  when tag is viewed face-on.
# X: right, Y: up, Z: out-of-tag (toward camera).
def _marker_obj_points(half: float) -> np.ndarray:
    return np.array([
        [-half,  half, 0.0],
        [ half,  half, 0.0],
        [ half, -half, 0.0],
        [-half, -half, 0.0],
    ], dtype=np.float32)


@dataclass
class MarkerLayout:
    marker_id: int
    registration_point_cm: list[float]
    yaw_deg: float


class LayoutCalibrator:
    """
    Accumulates N RGB frames, detects ArUco tags in each, then returns
    per-module world-space positions and yaw angles averaged over all frames.
    """

    def __init__(
        self,
        fx: float,
        fy: float,
        cx: float,
        cy: float,
        camera_transform: Transform,
        tag_size_cm: float,
        valid_marker_ids: set[int],
        n_frames: int = 30,
    ) -> None:
        self._camera_matrix = np.array(
            [[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=np.float64
        )
        self._dist = np.zeros(5, dtype=np.float64)
        self._camera_transform = camera_transform
        self._half_m = (tag_size_cm / 100.0) / 2.0
        self._obj_pts = _marker_obj_points(self._half_m)
        self._valid_ids = valid_marker_ids
        self._n_frames = n_frames

        aruco_dict = cv2.aruco.getPredefinedDictionary(_ARUCO_DICT_ID)
        params = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(aruco_dict, params)

        # marker_id -> list of (pos_world_cm [3], yaw_deg)
        self._acc: dict[int, list[tuple[np.ndarray, float]]] = {}
        self._frame_count = 0

    @property
    def frames_collected(self) -> int:
        return self._frame_count

    @property
    def n_frames(self) -> int:
        return self._n_frames

    def push(self, bgr_frame: np.ndarray) -> bool:
        """Process one BGR frame. Returns True once n_frames collected."""
        corners, ids, _ = self._detector.detectMarkers(bgr_frame)

        if ids is not None:
            for i, mid in enumerate(ids.flatten()):
                mid = int(mid)
                if mid not in self._valid_ids:
                    continue
                img_pts = corners[i].reshape(4, 2).astype(np.float32)
                ok, rvec, tvec = cv2.solvePnP(
                    self._obj_pts, img_pts, self._camera_matrix, self._dist,
                    flags=cv2.SOLVEPNP_IPPE_SQUARE,
                )
                if not ok:
                    continue
                pos_cm, yaw_deg = self._to_world(rvec.flatten(), tvec.flatten())
                self._acc.setdefault(mid, []).append((pos_cm, yaw_deg))

        self._frame_count += 1
        return self._frame_count >= self._n_frames

    def _to_world(self, rvec: np.ndarray, tvec: np.ndarray) -> tuple[np.ndarray, float]:
        """Convert PnP output (camera space, metres) to world pos + yaw."""
        # tvec: Orbbec camera space (X=right, Y=down, Z=forward), metres.
        # Axis remap to installation world coords (no scale yet):
        #   world X = cam X,   world Y = cam Z,   world Z = -cam Y
        pos_local_cm = np.array([
            tvec[0] * 100.0,
            tvec[2] * 100.0,
            -tvec[1] * 100.0,
        ])
        R_cam = rotator_to_matrix(self._camera_transform.rotation)
        pos_world = R_cam @ pos_local_cm + self._camera_transform.translation

        # Tag +Y axis = module forward direction.
        R_tag, _ = cv2.Rodrigues(rvec)
        tag_y_cam = R_tag[:, 1]
        tag_y_local = np.array([tag_y_cam[0], tag_y_cam[2], -tag_y_cam[1]])
        tag_y_world = R_cam @ tag_y_local

        # yaw: angle from world +Y (forward) toward +X (right)
        yaw_deg = float(math.degrees(math.atan2(tag_y_world[0], tag_y_world[1])))
        return pos_world, yaw_deg

    def build(self) -> dict[int, MarkerLayout]:
        """Return averaged MarkerLayout per detected marker_id."""
        results: dict[int, MarkerLayout] = {}
        for mid, readings in self._acc.items():
            pos_arr = np.array([r[0] for r in readings])
            yaw_arr = np.array([r[1] for r in readings])
            avg_pos = pos_arr.mean(axis=0)
            avg_yaw = float(math.degrees(math.atan2(
                np.mean(np.sin(np.radians(yaw_arr))),
                np.mean(np.cos(np.radians(yaw_arr))),
            )))
            results[mid] = MarkerLayout(
                marker_id=mid,
                registration_point_cm=[
                    round(float(avg_pos[0]), 1),
                    round(float(avg_pos[1]), 1),
                    round(float(avg_pos[2]), 1),
                ],
                yaw_deg=round(avg_yaw, 1),
            )
        return results


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def save_layout(
    results: dict[int, MarkerLayout],
    module_configs: list,
    output_path: Path,
) -> list[int]:
    """
    Write layout_calibrated.json. Returns list of missing marker IDs.
    Modules without a marker_id field are skipped silently.
    """
    modules_out: dict[str, dict] = {}
    missing: list[int] = []

    for mod in module_configs:
        mid = getattr(mod, "marker_id", None)
        if mid is None:
            continue
        if mid not in results:
            log.warning("marker_id=%d not detected — module keeps existing position", mid)
            missing.append(mid)
            continue
        layout = results[mid]
        modules_out[str(mid)] = {
            "registration_point_cm": layout.registration_point_cm,
            "rotation": {"yaw": layout.yaw_deg},
        }

    with open(output_path, "w") as f:
        json.dump({"modules": modules_out}, f, indent=2)

    n_total = sum(1 for m in module_configs if getattr(m, "marker_id", None) is not None)
    log.info(
        "Layout saved to %s  (%d/%d modules detected)",
        output_path, len(modules_out), n_total,
    )
    return missing


def apply_layout_overrides(settings: dict, layout_path: Path) -> dict:
    """
    Merge layout_calibrated.json into settings dict (deep copy).
    Only registration_point_cm and rotation.yaw are overridden per module.
    """
    if not layout_path.exists():
        return settings

    with open(layout_path) as f:
        layout = json.load(f)

    overrides = layout.get("modules", {})
    if not overrides:
        return settings

    import copy
    settings = copy.deepcopy(settings)
    for mod in settings.get("coordinator", {}).get("modules", []):
        mid = mod.get("marker_id")
        if mid is None:
            continue
        ov = overrides.get(str(mid))
        if ov is None:
            continue
        if "registration_point_cm" in ov:
            mod["registration_point_cm"] = ov["registration_point_cm"]
        if "rotation" in ov and "yaw" in ov["rotation"]:
            mod.setdefault("rotation", {})["yaw"] = ov["rotation"]["yaw"]

    log.info("Applied layout overrides from %s", layout_path)
    return settings
