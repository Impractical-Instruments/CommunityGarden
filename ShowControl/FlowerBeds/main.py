"""
Flower Beds — standalone Python show-control entry point.

Usage:
  # Run with real Orbbec camera, send OSC to Arduino, serve visualizer
  ShowControl main.py --config settings.json

  # Mock mode (no hardware) + visualizer only, no OSC
  ShowControl main.py --config settings.json --mock-camera --no-osc

  # Disable visualizer (headless show-computer mode)
  ShowControl main.py --config settings.json --no-visualizer
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

# IIVision lives at the repo root — two levels above ShowControl/FlowerBeds/
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from IIVision import MockCamera, OrbbecCamera, StabilizerConfig, Transform, Rotator, run_pipeline

from flower_beds import (
    Attraction,
    CameraConfig,
    ClusterConfig,
    Coordinator,
    CoordinatorConfig,
    ControllerConfig,
    ModuleConfig,
    MotorCommand,
)
from flower_controller import FlowerController

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


def parse_attraction_config(raw: dict) -> Attraction:
    return Attraction(
        influence_radius_cm=raw.get("influence_radius_cm", 300.0),
        distance_weight=raw.get("distance_weight", 1.0),
        distance_falloff_cm=raw.get("distance_falloff_cm", 150.0),
        dwell_weight=raw.get("dwell_weight", 0.5),
        dwell_halflife_frames=raw.get("dwell_halflife_frames", 30),
        inertia_weight=raw.get("inertia_weight", 0.3),
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


def parse_coordinator_config(raw: dict) -> CoordinatorConfig:
    return CoordinatorConfig(
        modules=parse_module_configs(raw.get("modules", [])),
        attraction=parse_attraction_config(raw.get("attraction", {})),
        exclusion_radius_cm=raw.get("cluster_exclusion_radius_cm", 0.0),
    )


def parse_controller_configs(raw_controllers: list[dict]) -> list[ControllerConfig]:
    return [ControllerConfig(ip=rc["ip"], port=rc["port"]) for rc in raw_controllers]


def parse_stabilizer_config(raw: dict) -> StabilizerConfig:
    return StabilizerConfig(
        max_match_dist_cm=raw.get("max_match_dist_cm", 80.0),
        smoothing_alpha=raw.get("smoothing_alpha", 0.3),
        max_miss_frames=raw.get("max_miss_frames", 8),
        min_confirm_frames=raw.get("min_confirm_frames", 2),
    )


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
    cam_cfg = parse_camera_config(raw_cameras[0])
    camera_transform = Transform(
        translation=np.array(cam_cfg.pos_cm, dtype=float),
        rotation=Rotator(**cam_cfg.rotation),
    )

    if args.mock_camera:
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
    coordinator = Coordinator.from_config(parse_coordinator_config(settings.get("coordinator", {})))
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

    # --- pipeline config ---
    calib_frames = settings.get("calibration_frames", 60)
    stab_cfg = parse_stabilizer_config(settings.get("stabilizer", {}))
    log.info(
        "Blob stabilizer: max_match_dist=%.0fcm alpha=%.2f miss=%d confirm=%d",
        stab_cfg.max_match_dist_cm,
        stab_cfg.smoothing_alpha,
        stab_cfg.max_miss_frames,
        stab_cfg.min_confirm_frames,
    )

    excl_filter = coordinator.make_exclusion_filter()

    # --- graceful shutdown ---
    _running = [True]

    def _stop(sig, frame):
        log.info("Shutting down…")
        _running[0] = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    frame_count = 0
    t_last_log = time.monotonic()

    for tracked in run_pipeline(camera, camera_transform, calib_frames, stab_cfg, excl_filter):
        if not _running[0]:
            break

        commands = coordinator.process_tracked_blobs(tracked)
        for ctrl in controllers:
            ctrl.send_all(commands)

        frame_count += 1
        broadcast({
            "frame": frame_count,
            "blobs": [
                {
                    "id": t.stable_id,
                    "x": float(t.world_pos_cm[0]),
                    "y": float(t.world_pos_cm[1]),
                }
                for t in tracked
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

        now = time.monotonic()
        if now - t_last_log >= 5.0:
            log.info("frame %d | tracked_blobs=%d", frame_count, len(tracked))
            t_last_log = now


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_calibrate(args: argparse.Namespace) -> None:
    """
    Calibration mode: command every motor to a fixed yaw so the physical
    flowers can be rotated to a known reference orientation.

    All motors are held at --calibrate-yaw degrees (default 0) until Ctrl+C.
    0° = forward (+Y world axis), 90° = right (+X), -90° = left.
    """
    settings = load_settings(args.config)
    yaw = args.calibrate_yaw

    # Collect every motor_id from config.
    motor_ids: list[int] = [
        cc["motor_id"]
        for rm in settings.get("modules", [])
        for cc in rm.get("clusters", [])
    ]
    if not motor_ids:
        log.error("No motors found in config")
        return

    commands = [MotorCommand(motor_id=mid, rotation_deg=yaw) for mid in motor_ids]

    controllers: list[FlowerController] = []
    if not args.no_osc:
        for ctrl_cfg in parse_controller_configs(settings.get("controllers", [])):
            controllers.append(FlowerController(ctrl_cfg))

    log.info(
        "Calibration mode — holding %d motor(s) at %.1f° (Ctrl+C to exit)",
        len(motor_ids), yaw,
    )
    log.info("Motor IDs: %s", motor_ids)
    if not controllers:
        log.info("(OSC disabled — no commands will be sent)")

    _running = [True]
    signal.signal(signal.SIGINT, lambda *_: _running.__setitem__(0, False))
    signal.signal(signal.SIGTERM, lambda *_: _running.__setitem__(0, False))

    while _running[0]:
        for ctrl in controllers:
            ctrl.send_all(commands)
        time.sleep(0.5)


def main() -> None:
    ap = argparse.ArgumentParser(description="Flower Beds standalone show control")
    ap.add_argument("--config", default="settings.json", help="Path to settings JSON")
    ap.add_argument("--mock-camera", action="store_true", help="Use mock camera (no hardware)")
    ap.add_argument("--no-osc", action="store_true", help="Disable OSC output")
    ap.add_argument("--no-visualizer", action="store_true", help="Disable remote visualizer")
    ap.add_argument("--visualizer-port", type=int, default=8765, help="Visualizer HTTP port")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument(
        "--calibrate-yaw", type=float, metavar="DEG", default=None,
        help="Calibration mode: hold all motors at this yaw (degrees) and exit when done. "
             "0=forward, 90=right, -90=left. No camera needed.",
    )
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.calibrate_yaw is not None:
        run_calibrate(args)
    else:
        run(args)


if __name__ == "__main__":
    main()
