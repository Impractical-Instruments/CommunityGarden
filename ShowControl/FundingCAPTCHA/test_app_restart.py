"""POST /api/restart restarts the camera and leaves the per-host settings override alone."""
import threading

import app


def test_restart_leaves_local_settings_untouched(tmp_path, monkeypatch):
    local = tmp_path / "captcha-settings.local.json"
    local.write_bytes(b'{"camera": {"serial": "ABC123"},\n "fps": 25}\n')
    before = local.read_bytes()
    monkeypatch.setattr(app, "SETTINGS_LOCAL", local)

    old_stop = threading.Event()
    cam = {"stop": old_stop, "thread": None}
    started = []
    app.restart_camera(cam, lambda: started.append(True))

    assert old_stop.is_set(), "the running camera thread must be told to stop"
    assert started == [True], "a fresh camera must be started"
    assert local.read_bytes() == before


def test_restart_does_not_create_a_local_settings_file(tmp_path, monkeypatch):
    local = tmp_path / "captcha-settings.local.json"
    monkeypatch.setattr(app, "SETTINGS_LOCAL", local)
    app.restart_camera({"stop": threading.Event(), "thread": None}, lambda: None)
    assert not local.exists()
