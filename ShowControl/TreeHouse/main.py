"""
TreeHouse show control — entry point.

Drives the per-frame update loop for all display elements:
  3× diorama boxes  (House Swarming, Mycellium, Club)
  2× garage windows (Looking Glass, Forge & Flora)
  2× gable windows  (Front Gable, Back Gable)
  1× dormer window  (Dormer)
"""

import argparse
import logging
import time

from coordinator import Coordinator, build_displays, load_config

log = logging.getLogger("treehouse")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TreeHouse show control")
    p.add_argument("--config", default="settings.json", help="Path to settings JSON")
    p.add_argument("--fps", type=int, default=30, help="Target update rate (default: 30)")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable DEBUG logging")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )

    config = load_config(args.config)
    displays = build_displays(config)
    coordinator = Coordinator(displays)

    log.info("TreeHouse show control starting — %d displays", len(displays))
    for name in coordinator.display_names:
        log.info("  • %s", name)

    dt = 1.0 / args.fps
    try:
        while True:
            t0 = time.monotonic()
            coordinator.update(dt)
            elapsed = time.monotonic() - t0
            remaining = dt - elapsed
            if remaining > 0:
                time.sleep(remaining)
    except KeyboardInterrupt:
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
