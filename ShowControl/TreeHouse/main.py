"""
TreeHouse show control — entry point.

Drives the per-frame update loop for all display elements:
  2× diorama boxes   (House Swarming, Club)
  2× garage windows  (Looking Glass, Forge & Flora)
  1× dormer window   (Dormer)

Receives OSC from the festival network to manage show modes.
Sends LED pixel data to the Pi Pico over USB serial each frame.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from branch_controller import BranchController
from coordinator import Coordinator, build_displays, load_config
from osc_server import serve as serve_osc
from pico_driver import PicoDriver
import visualizer

log = logging.getLogger("treehouse")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TreeHouse show control")
    p.add_argument("--config", default="settings.json", help="Path to settings JSON")
    p.add_argument("--no-pico", action="store_true", help="Skip Pico connection (dev mode)")
    p.add_argument("--no-branch", action="store_true", help="Skip branch controller connection (dev mode)")
    p.add_argument("--no-osc", action="store_true", help="Skip OSC listener")
    p.add_argument("--no-visualizer", action="store_true", help="Disable WebSocket visualizer server")
    p.add_argument("--visualizer-port", type=int, default=8766, metavar="N",
                   help="Visualizer HTTP port (default: 8766)")
    p.add_argument("--no-renderer", action="store_true", help="Skip Looking Glass renderer subprocess (dev mode)")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable DEBUG logging")
    return p.parse_args()


_RENDERER_PATH = Path(__file__).parent / "looking_glass" / "renderer.py"


async def _renderer_subprocess(renderer_path: Path) -> None:
    backoff = 1.0
    while True:
        log.info("Starting renderer subprocess")
        proc = await asyncio.create_subprocess_exec("/usr/bin/cage", "--", sys.executable, str(renderer_path))
        try:
            exit_code = await proc.wait()
        except asyncio.CancelledError:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
            raise
        if exit_code == 0:
            log.info("Renderer exited cleanly")
            return
        log.warning("Renderer crashed (exit %d), restarting in %.0fs", exit_code, backoff)
        try:
            await asyncio.sleep(backoff)
        except asyncio.CancelledError:
            raise
        backoff = min(backoff * 2, 30.0)


async def _frame_loop(
    coordinator: Coordinator,
    driver: PicoDriver,
    branch: BranchController,
    fps: int,
) -> None:
    dt = 1.0 / fps
    loop = asyncio.get_running_loop()
    frame = 0
    while True:
        t0 = loop.time()
        coordinator.update(dt)
        driver.send_frames(coordinator.get_all_frames(), coordinator.brightness)
        for motor_id, degrees in coordinator.get_branch_positions():
            branch.set_position(motor_id, degrees)
        frame += 1
        if frame % fps == 0:  # ~once per second
            await visualizer.broadcast_state(coordinator)
        await asyncio.sleep(max(0.0, dt - (loop.time() - t0)))


async def _run(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    displays = build_displays(config)
    coordinator = Coordinator(
        displays,
        branch_config=config.branch,
        heartbeat_interval_s=config.osc.heartbeat_interval_s,
    )
    coordinator._dim_level = config.show.dim_level

    driver = PicoDriver(config.pico.port, config.pico.baud)
    if not args.no_pico:
        driver.connect()

    branch = BranchController(config.branch.port, config.branch.baud)
    if not args.no_branch:
        branch.connect()

    log.info("TreeHouse starting — %d displays, %d branch motors",
             len(displays), len(config.branch.motors))
    for name in coordinator.display_names:
        log.info("  • %s", name)

    tasks = [asyncio.create_task(_frame_loop(coordinator, driver, branch, config.show.fps))]
    if not args.no_osc:
        tasks.append(asyncio.create_task(serve_osc(coordinator, config.osc.listen_port)))
    if not args.no_visualizer:
        tasks.append(asyncio.create_task(visualizer.serve(coordinator=coordinator, port=args.visualizer_port)))
    if not args.no_renderer:
        tasks.append(asyncio.create_task(_renderer_subprocess(_RENDERER_PATH)))

    try:
        await asyncio.gather(*tasks)
    finally:
        driver.close()
        branch.close()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
