from __future__ import annotations

import json
from pathlib import Path

# ShowControl/OSCFabric/ → ShowControl/network.json
_CANONICAL = Path(__file__).resolve().parent.parent / "network.json"


def load_network_config(path: str | Path | None = None) -> dict:
    """Load and return the parsed network.json.

    Pass *path* to override the canonical location (useful in tests).
    Raises FileNotFoundError if the file does not exist.
    """
    p = Path(path) if path is not None else _CANONICAL
    if not p.exists():
        raise FileNotFoundError(f"network.json not found at {p}")
    with open(p) as f:
        return json.load(f)
