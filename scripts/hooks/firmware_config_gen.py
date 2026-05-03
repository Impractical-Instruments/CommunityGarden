"""
PostToolUse hook: after network.json is edited, regenerate firmware config headers.
No-ops silently if the generator script doesn't exist yet.
"""

import json
import os
import subprocess
import sys

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "").replace("\\", "/")

if not file_path.endswith("ShowControl/network.json"):
    sys.exit(0)

gen_script = "scripts/generate_firmware_config.py"
if not os.path.exists(gen_script):
    sys.exit(0)

result = subprocess.run([sys.executable, gen_script], capture_output=True, text=True)
if result.returncode != 0:
    print(f"[firmware-config-gen] Failed:\n{result.stderr}", flush=True)
else:
    print("[firmware-config-gen] config.h files regenerated.", flush=True)
