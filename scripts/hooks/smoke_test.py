#!/usr/bin/env python3
"""
Post-write smoke test hook. Runs after every Write/Edit tool use.

Receives Claude Code hook JSON on stdin:
  {"tool_name": "Write", "tool_input": {"file_path": "...", ...}, ...}

Currently a stub — exits 0 always.
TODO: add fast import checks, syntax validation, or targeted unit runs.
"""
import json
import sys


def main() -> None:
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}
    _ = data.get("tool_input", {}).get("file_path", "")
    sys.exit(0)


if __name__ == "__main__":
    main()
