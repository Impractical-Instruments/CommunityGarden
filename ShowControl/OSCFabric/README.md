# OSCFabric

The sender side of the OSC Fabric, and the one reader of `ShowControl/network.json`. Installed as the `OSCFabric` package (`pyproject.toml` at the repo root).

- **`FabricClient(element, config)`** sends an Element's signals to the TreeHouse (ADR-0007). `config` is the parsed `network.json`:
  - `report(signal, value)` sends on first call and when the value changes by more than `change_epsilon`.
  - `send_event(event)` always sends (one-shot events such as a Blow-Up).
  - `tick(dt)` re-sends every tracked signal once per `heartbeat_interval_s`.
- **`load_network_config(path=None)`** returns the parsed `network.json`; raises `FileNotFoundError` if it is missing.
- **`load_network_config_or_empty(log, path=None)`** warns and returns `{}` instead, for callers that can run without it.

Every network address comes from `network.json` through these functions; nothing else resolves its path (AGENTS.md constraint 3).

Only the TreeHouse receives Fabric messages; its listener is `ShowControl/TreeHouse/osc_server.py`.

**Tests:** `test_client.py`; `uv run pytest ShowControl/OSCFabric`.
