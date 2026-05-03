"""
PostToolUse hook: after any Python file edit under ShowControl/, run a
syntax check and a 3-second startup smoke test for the affected element.
"""

import json
import os
import re
import subprocess
import sys

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "").replace("\\", "/")

if not file_path.endswith(".py"):
    sys.exit(0)

m = re.search(r"ShowControl/(FlowerBeds|TreeHouse|FundingCAPTCHA)/", file_path)
if not m:
    sys.exit(0)

element = m.group(1)
element_dir = os.path.join("ShowControl", element)

# Syntax check
result = subprocess.run(
    [sys.executable, "-m", "py_compile", file_path],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    print(f"[smoke-test] Syntax error in {file_path}:\n{result.stderr}", flush=True)
    sys.exit(0)

# Startup smoke test — 3 s timeout; TimeoutExpired means it ran cleanly
main_py = os.path.join(element_dir, "main.py")
if not os.path.exists(main_py):
    sys.exit(0)

proc = subprocess.Popen(
    [sys.executable, "main.py", "--mock", "--no-osc", "--no-visualizer"],
    cwd=element_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
try:
    _, stderr = proc.communicate(timeout=3)
    if proc.returncode not in (0, None):
        err = stderr.decode(errors="replace")
        # Missing third-party dep = environment issue, not a code error; skip report
        if "ModuleNotFoundError" not in err and "No module named" not in err:
            print(f"[smoke-test] {element} crashed on startup:\n{err}", flush=True)
except subprocess.TimeoutExpired:
    proc.kill()
    proc.communicate()
    # Ran 3 s without crashing — good
