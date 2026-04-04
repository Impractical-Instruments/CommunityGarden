"""
Flower Beds — standalone Python show-control entry point.

Usage:
  # Run with real Orbbec camera, send OSC to Arduino, serve visualizer
  python main.py --config settings.json

  # Mock mode (no hardware) + visualizer only, no OSC
  python main.py --config settings.json --mock --no-osc

  # Disable visualizer (headless show-computer mode)
  python main.py --config settings.json --no-visualizer
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import time
from pathlib import Path

import numpy as np

from blob_tracker import BlobTracker, CalibrationState
from camera import MockCamera, OrbbecCamera
from flower_beds import CameraConfig, ClusterConfig, Coordinator, ControllerConfig, ModuleConfig
from flower_controller import FlowerController
from transforms import UERotator, UETransform

log = logging.getLogger("flower_beds")


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_settings(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def parse_camera_config(raw: dict) -> CameraConfig:
    return CameraConfig(
        name=raw.get("name", ""),
        pos_cm=raw.get("pos_cm", [0, 0, 0]),
        rotation=raw.get("rotation", {"pitch": 0, "yaw": 0, "roll": 0}),
        serial=raw.get("serial", ""),
        width=raw.get("width", 640),
        height=raw.get("height", 400),
        framerate=raw.get("framerate", 30),
    )


def parse_module_configs(raw_modules: list[dict]) -> list[ModuleConfig]:
    modules = []
    for rm in raw_modules:
        clusters = [
            ClusterConfig(
                motor_id=rc["motor_id"],
                pos_offset_cm=rc.get("pos_offset_cm", [0, 0, 0]),
                rotation_offset=rc.get("rotation_offset", {"pitch": 0, "yaw": 0, "roll": 0}),
            )
            for rc in rm.get("clusters", [])
        ]
        modules.append(ModuleConfig(
            registration_point_cm=rm.get("registration_point_cm", [0, 0, 0]),
            rotation=rm.get("rotation", {"pitch": 0, "yaw": 0, "roll": 0}),
            clusters=clusters,
        ))
    return modules


def parse_controller_configs(raw_controllers: list[dict]) -> list[ControllerConfig]:
    return [ControllerConfig(ip=rc["ip"], port=rc["port"]) for rc in raw_controllers]


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    settings = load_settings(args.config)

    # --- camera ---
    raw_cameras = settings.get("cameras", [])
    if not raw_cameras:
        log.error("No cameras defined in settings")
        sys.exit(1)
    # Currently supporting one camera (same as the single-tracker UE setup)
    cam_cfg = parse_camera_config(raw_cameras[0])
    camera_transform = UETransform(
        translation=np.array(cam_cfg.pos_cm, dtype=float),
        rotation=UERotator(**cam_cfg.rotation),
    )

    if args.mock:
        camera = MockCamera(width=cam_cfg.width, height=cam_cfg.height, fps=cam_cfg.framerate)
        log.info("Using mock camera")
    else:
        camera = OrbbecCamera(
            serial=cam_cfg.serial or None,
            width=cam_cfg.width,
            height=cam_cfg.height,
            fps=cam_cfg.framerate,
        )
        log.info("Using Orbbec camera serial=%s", cam_cfg.serial)

    # --- coordinator ---
    module_configs = parse_module_configs(settings.get("modules", []))
    coordinator = Coordinator.from_config(module_configs)
    log.info("Loaded %d module(s), %d cluster(s) total",
             len(coordinator.modules),
             sum(len(m.clusters) for m in coordinator.modules))

    # --- OSC controllers ---
    controllers: list[FlowerController] = []
    if not args.no_osc:
        for ctrl_cfg in parse_controller_configs(settings.get("controllers", [])):
            controllers.append(FlowerController(ctrl_cfg))
        log.info("OSC output → %d controller(s)", len(controllers))
    else:
        log.info("OSC output disabled (--no-osc)")

    # --- visualizer ---
    if not args.no_visualizer:
        from visualizer import broadcast, start_server
        start_server(host="0.0.0.0", port=args.visualizer_port)
    else:
        def broadcast(_state):  # noqa: F811
            pass

    # --- blob tracker ---
    tracker = BlobTracker()
    calib_frames = settings.get("calibration_frames", 60)

    # --- graceful shutdown ---
    _running = [True]

    def _stop(sig, frame):
        log.info("Shutting down…")
        _running[0] = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    frame_count = 0
    t_last_log = time.monotonic()

    with camera:
        for frame in camera.frames():
            if not _running[0]:
                break

            # Drive calibration state machine (mirrors OrbbecBlobTracker::OnFramesReceived)
            if tracker.state == CalibrationState.NOT_CALIBRATED:
                tracker.begin_calibration(calib_frames, frame.width, frame.height)
                tracker.push_calibration_frame(frame)

            elif tracker.state == CalibrationState.IN_PROGRESS:
                tracker.push_calibration_frame(frame)

            else:  # CALIBRATED
                result = tracker.detect(frame)

                commands = coordinator.process_blobs(camera_transform, result.world_blobs)

                for ctrl in controllers:
                    ctrl.send_all(commands)

                frame_count += 1

                # Build visualizer state
                broadcast({
                    "frame": frame_count,
                    "calibration_state": tracker.state.value,
                    "blobs": [
                        {
                            "id": b.id,
                            "x": float(b.world_pos_cm()[0]),
                            "y": float(b.world_pos_cm()[1]),
                        }
                        for b in result.world_blobs
                        if b.valid
                    ],
                    "clusters": coordinator.snapshot(),
                    "cameras": [
                        {
                            "name": cam_cfg.name,
                            "x": float(cam_cfg.pos_cm[0]),
                            "y": float(cam_cfg.pos_cm[1]),
                            "yaw_deg": float(cam_cfg.rotation.get("yaw", 0)),
                        }
                    ],
                })

            # Periodic log
            now = time.monotonic()
            if now - t_last_log >= 5.0:
                n_blobs = len(result.world_blobs) if tracker.state == CalibrationState.CALIBRATED else 0
                log.info("frame %d | %s | blobs=%d",
                         frame_count, tracker.state.value, n_blobs)
                t_last_log = now


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Flower Beds standalone show control")
    ap.add_argument("--config", default="settings.json", help="Path to settings JSON")
    ap.add_argument("--mock", action="store_true", help="Use mock camera (no hardware)")
    ap.add_argument("--no-osc", action="store_true", help="Disable OSC output")
    ap.add_argument("--no-visualizer", action="store_true", help="Disable remote visualizer")
    ap.add_argument("--visualizer-port", type=int, default=8765, help="Visualizer HTTP port")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    run(args)


if __name__ == "__main__":
    main()
