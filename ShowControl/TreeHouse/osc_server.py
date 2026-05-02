"""
OSC server — receives show-control messages from other festival elements.

Recognised addresses
--------------------
/treehouse/mode        <string>   "full" | "dim" | "off"
/treehouse/brightness  <float>    0.0–1.0  (overrides the dim level in config)
/flowerbeds/activity   <float>    0.0–1.0  normalised visitor activity from FlowerBeds
/captcha/intensity     <float>    0.0–1.0  Arc progress toward Blow-Up from FundingCAPTCHA
/captcha/blowup                   one-shot Blow-Up event from FundingCAPTCHA
/pipes/activity        <float>    0.0–1.0  normalised music engagement from Playing the Pipes
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

if TYPE_CHECKING:
    from coordinator import Coordinator

log = logging.getLogger("treehouse")


def _build_dispatcher(coordinator: "Coordinator") -> Dispatcher:
    d = Dispatcher()

    def on_mode(address: str, mode: str) -> None:
        log.info("OSC %s → %r", address, mode)
        coordinator.set_mode(mode)

    def on_brightness(address: str, level: float) -> None:
        log.info("OSC %s → %.2f", address, level)
        coordinator.set_dim_level(float(level))

    def on_flowerbeds_activity(address: str, value: float) -> None:
        coordinator.set_flowerbeds_activity(float(value))

    def on_captcha_intensity(address: str, value: float) -> None:
        coordinator.set_captcha_intensity(float(value))

    def on_captcha_blowup(address: str, *args) -> None:
        log.info("OSC %s — captcha blowup", address)
        coordinator.trigger_captcha_blowup()

    def on_pipes_activity(address: str, value: float) -> None:
        coordinator.set_pipes_activity(float(value))

    d.map("/treehouse/mode", on_mode)
    d.map("/treehouse/brightness", on_brightness)
    d.map("/flowerbeds/activity", on_flowerbeds_activity)
    d.map("/captcha/intensity", on_captcha_intensity)
    d.map("/captcha/blowup", on_captcha_blowup)
    d.map("/pipes/activity", on_pipes_activity)
    d.set_default_handler(
        lambda addr, *args: log.debug("OSC unhandled: %s %s", addr, args)
    )
    return d


async def serve(coordinator: "Coordinator", port: int) -> None:
    loop = asyncio.get_running_loop()
    dispatcher = _build_dispatcher(coordinator)
    server = AsyncIOOSCUDPServer(("0.0.0.0", port), dispatcher, loop)
    transport, _ = await server.create_serve_endpoint()
    log.info("OSC server listening on :%d", port)
    try:
        await asyncio.sleep(float("inf"))
    finally:
        transport.close()
