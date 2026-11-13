"""The shader and playlist players stand on the shared modules, never on the kiosk's app.py (#245)."""
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize("module", ["shader_stage", "playlist_app", "video_player"])
def test_player_does_not_import_the_kiosk(module):
    probe = f"import sys, {module}; sys.exit('app' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", probe], cwd=HERE,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, (
        f"importing {module} pulled in app.py\n{result.stderr}")
