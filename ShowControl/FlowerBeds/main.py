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
import logging
import sys
import time
from pathlib import Path

import numpy as np

from IIVision import (
    MockCamera, OrbbecCamera, StabilizerConfig, Transform, Rotator,
    Calibration, build_calibration, run_pipeline,
)

from config import CameraConfig, CoordinatorConfig, load_settings
from controllers import ControllerBus
from flower_beds import Coordinator
from state import build_visualizer_state
from stop_signal import StopSignal

from OSCFabric import FabricClient, load_network_config_or_empty

log = logging.getLogger("flower_beds")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    settings = load_settings(args.config)
    network = load_network_config_or_empty(log)

    # --- camera config (shared across restarts) ---
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
            width=cam_cfg.width, height=cam_cfg.height, fps=cam_cfg.framerate,
            mirror=cam_cfg.mirror,
        )
        log.info("Using Orbbec camera (auto-discover, mirror=%s)", cam_cfg.mirror)

    # --- OSC controllers (servo hardware) ---
    bus = ControllerBus([]) if args.no_osc else ControllerBus.from_network(network)
    if len(bus):
        log.info("OSC output → %d controller(s)", len(bus))
    else:
        log.info("OSC output disabled (--no-osc)")

    # --- diagnose: ping each controller, surface missing motor IDs ---
    coord_cfg_preview = CoordinatorConfig.from_dict(settings.get("coordinator", {}))
    expected_motor_ids: set[int] = {c.motor_id for c in coord_cfg_preview.all_clusters()}
    if len(bus):
        missing_motor_ids = bus.diagnose(expected_motor_ids)
    else:
        missing_motor_ids = []

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

    # --- graceful shutdown ---
    stop = StopSignal("Shutting down…")

    # --- depth calibration (persisted, reused across restarts) ---
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

    # --- outer restart loop (re-enters if pipeline exits unexpectedly) ---
    while not stop:
        coordinator = Coordinator.from_config(
            CoordinatorConfig.from_dict(settings.get("coordinator", {}))
        )
        log.info(
            "Coordinator: %d module(s), %d cluster(s)",
            len(coordinator.modules),
            sum(len(m.clusters) for m in coordinator.modules),
        )
        excl_filter = coordinator.make_exclusion_filter()

        frame_count = 0
        t_last_log = time.monotonic()

        for tracked in run_pipeline(camera, camera_transform, calibration, stab_cfg, excl_filter):
            if stop:
                break

            commands = coordinator.process_tracked_blobs(tracked)
            for cmd in commands:
                bus.send(cmd.motor_id, cmd.rotation_deg)

            if fabric is not None:
                activity = min(1.0, len(tracked) / activity_max_blobs)
                fabric.report("activity", activity)
                fabric.tick(1.0 / cam_cfg.framerate)

            frame_count += 1
            state = build_visualizer_state(
                frame_count, tracked, coordinator.snapshot(), cam_cfg, missing_motor_ids,
            )
            broadcast(state)

            now = time.monotonic()
            if now - t_last_log >= 5.0:
                log.info("frame %d | tracked_blobs=%d", frame_count, len(tracked))
                t_last_log = now


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    run(args)


if __name__ == "__main__":
    main()
