#!/usr/bin/env python3
"""
Regenerates firmware config headers from network.json after any write that touches it.
Runs after every Write/Edit tool use; exits immediately if network.json was not changed.

See docs/adr/0007-osc-fabric-schema.md for rationale.

TODO: generate Firmware/FlowerBeds_Follow_ServoController/config.h from network.json.
"""
import json
import sys


def main() -> None:
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}
    file_path = data.get("tool_input", {}).get("file_path", "")

    if "network.json" not in file_path:
        sys.exit(0)

    # TODO: parse network.json and emit config.h for each firmware target
    print("network.json changed — firmware config.h generation not yet implemented", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
