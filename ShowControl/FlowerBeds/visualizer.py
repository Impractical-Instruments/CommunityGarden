"""
Remote visualizer for the FlowerBeds Element: the state `main.py` pushes each frame, on a LiveServer.

Open  http://<show-computer-ip>:<port>  to see a live top-down view of blobs, clusters,
and camera positions. The page is visualizer_static/index.html.
"""

from __future__ import annotations

from pathlib import Path

from ShowWeb import LiveServer

from state import VisualizerState

_server = LiveServer("flower_beds", html=Path(__file__).parent / "visualizer_static" / "index.html")


def broadcast(state: VisualizerState) -> None:
    """Thread-safe: push a state snapshot to all connected browsers. Call from the frame loop."""
    _server.broadcast(state)


def start_server(host: str, port: int) -> None:
    """Launch the server in a background daemon thread and return."""
    _server.start_in_thread(host=host, port=port)
    print(f"Visualizer: http://{host}:{port}")
