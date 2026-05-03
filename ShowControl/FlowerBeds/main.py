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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from visualizer import VisualizerState

import numpy as np

# IIVision lives at the repo root — two levels above ShowControl/FlowerBeds/
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from IIVision import (
    MockCamera, OrbbecCamera, StabilizerConfig, Transform, Rotator,
    Calibration, build_calibration, run_pipeline,
)

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
from pythonosc.udp_client import SimpleUDPClient  # type: ignore[import]

# OSCFabric lives one level above FlowerBeds, inside ShowControl/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from OSCFabric import FabricClient, load_network_config

_OSC_ADDRESS = "/cg/ff/rot"

log = logging.getLogger("flower_beds")


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_settings(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_controllers(network: dict, no_osc: bool) -> list[SimpleUDPClient]:
    if no_osc:
        return []
    clients = []
    for key, fw in network.get("firmware", {}).items():
        if key.startswith("flowerbeds_controller_") and fw.get("ip") and fw.get("osc_port"):
            clients.append(SimpleUDPClient(fw["ip"], fw["osc_port"]))
    return clients


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    settings = load_settings(args.config)
    try:
        network = load_network_config()
    except FileNotFoundError as exc:
        log.warning("%s — OSC fabric disabled", exc)
        network = {}

    # --- camera ---
    raw_cameras = settings.get("cameras", [])
    if not raw_cameras:
        log.error("No cameras defined in settings")
        sys.exit(1)
    cam_cfg = CameraConfig.from_dict(raw_cameras[0])
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
    coordinator = Coordinator.from_config(CoordinatorConfig.from_dict(settings.get("coordinator", {})))
    log.info("Loaded %d module(s), %d cluster(s) total",
             len(coordinator.modules),
             sum(len(m.clusters) for m in coordinator.modules))

    # --- OSC controllers (servo hardware) ---
    controllers = _build_controllers(network, args.no_osc)
    if controllers:
        log.info("OSC output → %d controller(s)", len(controllers))
    else:
        log.info("OSC output disabled (--no-osc)")

    # --- OSC fabric (TreeHouse activity signal) ---
    activity_max_blobs = settings.get("activity_max_blobs", 10)
    fabric: FabricClient | None = None
    if not args.no_osc and network.get("elements", {}).get("treehouse", {}).get("ip"):
        fabric = FabricClient("flowerbeds", network)
        th = network["elements"]["treehouse"]
        log.info("OSC fabric → TreeHouse %s:%d", th["ip"], th["osc_port"])

    # --- visualizer ---
    if not args.no_visualizer:
        from visualizer import broadcast, start_server
        start_server(host="0.0.0.0", port=args.visualizer_port)
    else:
        def broadcast(_state):  # noqa: F811
            pass

    # --- pipeline config ---
    calib_frames = settings.get("calibration_frames", 60)
    stab_cfg = StabilizerConfig.from_dict(settings.get("stabilizer", {}))
    log.info(
        "Blob stabilizer: max_match_dist=%.0fcm alpha=%.2f miss=%d confirm=%d",
        stab_cfg.max_match_dist_cm,
        stab_cfg.smoothing_alpha,
        stab_cfg.max_miss_frames,
        stab_cfg.min_confirm_frames,
    )

    excl_filter = coordinator.make_exclusion_filter()

    # --- calibration ---
    calib_path = Path(args.config).with_suffix(".calibration.npz")
    calibration: Calibration | None = None
    if not args.recalibrate and calib_path.exists():
        try:
            calibration = Calibration.load(calib_path)
            log.info("Loaded calibration from %s", calib_path)
        except Exception as exc:
            log.warning("Calibration load failed (%s) — recalibrating", exc)

    if calibration is None:
        calibration = build_calibration(camera, calib_frames)
        calibration.save(calib_path)
        log.info("Calibration saved to %s", calib_path)

    calibration_state = "calibrated"

    # --- graceful shutdown ---
    _running = True

    def _stop(sig, frame):
        nonlocal _running
        log.info("Shutting down…")
        _running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    frame_count = 0
    t_last_log = time.monotonic()

    for tracked in run_pipeline(camera, camera_transform, calibration, stab_cfg, excl_filter):
        if not _running:
            break

        commands = coordinator.process_tracked_blobs(tracked)
        for ctrl in controllers:
            for cmd in commands:
                ctrl.send_message(_OSC_ADDRESS, cmd.to_osc_args())

        if fabric is not None:
            activity = min(1.0, len(tracked) / activity_max_blobs)
            fabric.report("activity", activity)
            fabric.tick(1.0 / cam_cfg.framerate)

        frame_count += 1
        state: VisualizerState = {
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
            "calibration_state": calibration_state,
        }
        broadcast(state)

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
    try:
        network = load_network_config()
    except FileNotFoundError as exc:
        log.warning("%s — OSC fabric disabled", exc)
        network = {}
    yaw = args.calibrate_yaw

    # Collect every motor_id from config.
    coordinator_cfg = CoordinatorConfig.from_dict(settings.get("coordinator", {}))
    motor_ids: list[int] = [
        cluster.motor_id
        for module in coordinator_cfg.modules
        for cluster in module.clusters
    ]
    if not motor_ids:
        log.error("No motors found in config")
        return

    commands = [MotorCommand(motor_id=mid, rotation_deg=yaw) for mid in motor_ids]

    controllers = _build_controllers(network, args.no_osc)

    log.info(
        "Calibration mode — holding %d motor(s) at %.1f° (Ctrl+C to exit)",
        len(motor_ids), yaw,
    )
    log.info("Motor IDs: %s", motor_ids)
    if not controllers:
        log.info("(OSC disabled — no commands will be sent)")

    _running = True

    def _stop(*_):
        nonlocal _running
        _running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    while _running:
        for ctrl in controllers:
            for cmd in commands:
                ctrl.send_message(_OSC_ADDRESS, cmd.to_osc_args())
        time.sleep(0.5)


def main() -> None:
    ap = argparse.ArgumentParser(description="Flower Beds standalone show control")
    ap.add_argument("--config", default="settings.json", help="Path to settings JSON")
    ap.add_argument("--mock-camera", action="store_true", help="Use mock camera (no hardware)")
    ap.add_argument("--no-osc", action="store_true", help="Disable OSC output")
    ap.add_argument("--no-visualizer", action="store_true", help="Disable remote visualizer")
    ap.add_argument("--visualizer-port", type=int, default=8765, help="Visualizer HTTP port")
    ap.add_argument("--recalibrate", action="store_true",
                    help="Ignore saved calibration and recalibrate from scratch")
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
