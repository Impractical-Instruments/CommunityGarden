"""
TreeHouse visualizer: the show state snapshot and the /control/* routes, on a LiveServer.

Access: http://<show-computer-ip>:<port>
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request  # type: ignore[import]

from ShowWeb import LiveServer

if TYPE_CHECKING:
    from coordinator import Coordinator

log = logging.getLogger("treehouse")

_coordinator: "Coordinator | None" = None


# ---------------------------------------------------------------------------
# Control endpoints — test dashboard → coordinator
# ---------------------------------------------------------------------------

def _control_routes(app: FastAPI) -> None:
    @app.post("/control/show/mode")
    async def ctrl_show_mode(req: Request):
        body = await req.json()
        if _coordinator:
            _coordinator.set_mode(body["mode"])
        return {"ok": True}

    @app.post("/control/show/brightness")
    async def ctrl_show_brightness(req: Request):
        body = await req.json()
        if _coordinator:
            _coordinator.set_dim_level(float(body["level"]))
        return {"ok": True}

    @app.post("/control/looking-glass")
    async def ctrl_looking_glass(req: Request):
        body = await req.json()
        if _coordinator:
            _coordinator.set_looking_glass_scene(body["scene"])
        return {"ok": True}

    @app.post("/control/blowup")
    async def ctrl_blowup():
        """Fire the Blow-Up one-shot, as /captcha/blowup does."""
        if _coordinator:
            _coordinator.intake.trigger_captcha_blowup()
        return {"ok": True}


_server = LiveServer("treehouse", extra_routes=_control_routes)
app = _server.app


# ---------------------------------------------------------------------------
# State broadcast — called from the frame loop coroutine
# ---------------------------------------------------------------------------

async def broadcast_state(coordinator: Coordinator) -> None:
    if not _server.has_clients:
        return
    await _server.broadcast_async({
        "mode": coordinator.mode.value,
        "brightness": coordinator.brightness,
        "controllables": [
            {"name": s.name, "enabled": s.enabled, "params": s.params}
            for s in coordinator.get_all_states()
        ],
    })


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

async def serve(coordinator: "Coordinator | None", port: int, host: str = "0.0.0.0") -> None:
    """Run the server as an asyncio task in the caller's event loop."""
    global _coordinator
    _coordinator = coordinator
    log.info("TreeHouse visualizer: http://%s:%d", host, port)
    await _server.serve(host=host, port=port)
