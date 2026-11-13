"""
Motor calibration command-line tool: hold or sweep every motor, no camera or vision.

Usage (from ShowControl/FlowerBeds/):
  # Hold every motor at one yaw (0=forward, 90=right, -90=left) until Ctrl+C
  uv run python calibrate_motors.py --config settings.json --yaw 0

  # Sweep every motor through -limit, 0, +limit, 0 until Ctrl+C
  uv run python calibrate_motors.py --config settings.json --sweep
"""

from __future__ import annotations

import argparse
import logging
import time

from config import CoordinatorConfig, load_settings
from controllers import ControllerBus
from flower_beds import MotorCommand
from OSCFabric import load_network_config_or_empty
from stop_signal import StopSignal

log = logging.getLogger("flower_beds")


def _make_bus(network: dict, no_osc: bool) -> ControllerBus:
    return ControllerBus([]) if no_osc else ControllerBus.from_network(network)


def _send(bus: ControllerBus, commands: list[MotorCommand]) -> None:
    for cmd in commands:
        bus.send(cmd.motor_id, cmd.rotation_deg)


def run_hold(args: argparse.Namespace) -> None:
    """
    Command every motor to a fixed yaw so the physical flowers can be rotated
    to a known reference orientation.

    All motors are held at --yaw degrees until Ctrl+C.
    0° = forward (+Y world axis), 90° = right (+X), -90° = left.
    """
    settings = load_settings(args.config)
    network = load_network_config_or_empty(log)
    yaw = args.yaw

    coordinator_cfg = CoordinatorConfig.from_dict(settings.get("coordinator", {}))
    motor_ids: list[int] = [cluster.motor_id for cluster in coordinator_cfg.all_clusters()]
    if not motor_ids:
        log.error("No motors found in config")
        return

    commands = [MotorCommand(motor_id=mid, rotation_deg=yaw) for mid in motor_ids]

    bus = _make_bus(network, args.no_osc)

    log.info(
        "Calibration mode — holding %d motor(s) at %.1f° (Ctrl+C to exit)",
        len(motor_ids), yaw,
    )
    log.info("Motor IDs: %s", motor_ids)
    if not len(bus):
        log.info("(OSC disabled — no commands will be sent)")

    stop = StopSignal()
    while not stop:
        _send(bus, commands)
        time.sleep(0.5)


def run_sweep(args: argparse.Namespace) -> None:
    """
    Sweep every motor through -yaw_limit_deg, 0, +yaw_limit_deg, 0 at a fixed
    period.  Crew watches the physical motion to confirm per-cluster limits
    match physical travel before showtime.

    Each cluster uses ITS OWN yaw_limit_deg from settings.json — so a cluster
    that has been locally tightened in the layout tool will sweep within the
    tighter cone, not the global default.
    """
    settings = load_settings(args.config)
    network = load_network_config_or_empty(log)

    coordinator_cfg = CoordinatorConfig.from_dict(settings.get("coordinator", {}))
    # (motor_id, yaw_limit_deg) for every cluster.
    motors: list[tuple[int, float]] = [
        (cluster.motor_id, float(cluster.yaw_limit_deg))
        for cluster in coordinator_cfg.all_clusters()
    ]
    if not motors:
        log.error("No motors found in config")
        return

    bus = _make_bus(network, args.no_osc)

    period_s = max(0.5, args.sweep_period_s)
    phase_s  = period_s / 4.0

    log.info(
        "Sweep mode — %d motor(s), %.1fs period (±limit → 0 → +limit → 0). Ctrl+C to exit.",
        len(motors), period_s,
    )
    log.info("Motor IDs + limits: %s", motors)
    if not len(bus):
        log.info("(OSC disabled — no commands will be sent)")

    stop = StopSignal()
    # 4-phase cycle scaled per-motor by its own yaw_limit_deg.
    phase_scales = [-1.0, 0.0, 1.0, 0.0]
    phase_idx = 0
    while not stop:
        scale = phase_scales[phase_idx]
        _send(bus, [
            MotorCommand(motor_id=mid, rotation_deg=scale * limit)
            for mid, limit in motors
        ])
        log.info("phase %d/4 — scale=%+.1f × limit", phase_idx + 1, scale)
        time.sleep(phase_s)
        phase_idx = (phase_idx + 1) % 4


def main() -> None:
    ap = argparse.ArgumentParser(description="Flower Beds motor calibration (no camera needed)")
    ap.add_argument("--config", default="settings.json", help="Path to settings JSON")
    ap.add_argument("--no-osc", action="store_true", help="Disable OSC output (dry run)")
    ap.add_argument("--verbose", "-v", action="store_true")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--yaw", type=float, metavar="DEG",
        help="Hold all motors at this yaw (degrees) until Ctrl+C. 0=forward, 90=right, -90=left.",
    )
    mode.add_argument(
        "--sweep", action="store_true",
        help="Cycle every motor through -limit, 0, +limit, 0 forever "
             "so the crew can verify each cluster's yaw_limit_deg on site.",
    )
    ap.add_argument(
        "--sweep-period-s", type=float, default=4.0,
        help="Seconds for one full sweep cycle in --sweep mode (default 4.0).",
    )
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.sweep:
        run_sweep(args)
    else:
        run_hold(args)


if __name__ == "__main__":
    main()
