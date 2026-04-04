"""
FundingCAPTCHA — depth-camera touch detection entry point.

State machine:
    BACKGROUND_CALIBRATION  →  CORNER_CALIBRATION  →  RUNNING
         (auto, N frames)        (4 user touches)

If a saved calibration file exists and --recalibrate is not passed, corner
calibration is skipped and the system goes straight to RUNNING.

Usage:
    python main.py [--config settings.json] [--mock] [--recalibrate] [--no-osc]
                   [--no-visualizer] [--visualizer-port 8766] [-v]
"""

from __future__ import annotations

import argparse
import enum
import json
import logging
import signal
import sys
import threading
import time
from pathlib import Path

import numpy as np

from calibration import ScreenCalibration
from camera import MockCamera, OrbbecCamera
from touch_detector import CalibrationState, TouchDetector
from touch_tracker import EventType, GridTouchTracker

log = logging.getLogger("touch_screen")


# ---------------------------------------------------------------------------
# Top-level state
# ---------------------------------------------------------------------------

class AppState(enum.Enum):
    BACKGROUND_CALIBRATION = "background_calibration"
    CORNER_CALIBRATION = "corner_calibration"
    RUNNING = "running"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_settings(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# OSC helpers
# ---------------------------------------------------------------------------

def make_osc_client(ip: str, port: int):
    from pythonosc.udp_client import SimpleUDPClient  # type: ignore[import]
    return SimpleUDPClient(ip, port)


def start_osc_server(port: int, grid_size_callback, recalibrate_callback) -> None:
    """Start an OSC receive server in a background daemon thread."""
    from pythonosc.dispatcher import Dispatcher  # type: ignore[import]
    from pythonosc.osc_server import ThreadingOSCUDPServer  # type: ignore[import]

    dispatcher = Dispatcher()
    dispatcher.map("/captcha/grid_size", grid_size_callback)
    dispatcher.map("/captcha/recalibrate", recalibrate_callback)

    server = ThreadingOSCUDPServer(("0.0.0.0", port), dispatcher)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    log.info("OSC receive server on port %d", port)


# ---------------------------------------------------------------------------
# Corner calibration helper
# ---------------------------------------------------------------------------

def run_corner_calibration(
    detector: TouchDetector,
    calibration: ScreenCalibration,
    camera_frames,
    osc_client,
    running_flag: list[bool],
    broadcast_fn=None,
) -> bool:
    """
    Step through the 4-corner calibration sequence.

    For each corner:
      1. Send /captcha/cal/prompt idx uv_x uv_y to Godot.
      2. Wait for the user to lift any previous touch (clear baseline).
      3. Detect the first new touch and record its centroid.
      4. Send /captcha/cal/ack idx.

    Returns True on success, False if interrupted.
    """
    log.info("Starting corner calibration — follow the on-screen prompts")

    while not calibration.is_complete:
        idx  = calibration.next_corner_index
        uv   = calibration.next_corner_uv
        name = calibration.next_corner_name

        log.info("Corner %d/4 — touch the %s marker", idx + 1, name)
        if osc_client:
            osc_client.send_message("/captcha/cal/prompt", [idx, float(uv[0]), float(uv[1])])

        # Single inner loop — phase variable drives the two-phase logic.
        phase = "clearing"   # wait until no touches, then switch to "waiting"
        for frame in camera_frames:
            if not running_flag[0]:
                return False
            touches = detector.detect(frame)
            if broadcast_fn:
                broadcast_fn(touches)
            if phase == "clearing":
                if not touches:
                    phase = "waiting"
            else:  # "waiting"
                if touches:
                    best = max(touches, key=lambda t: t.pixel_count)
                    calibration.add_corner(best.pixel_x, best.pixel_y)
                    log.info(
                        "  Corner %d recorded at pixel (%.1f, %.1f)",
                        idx, best.pixel_x, best.pixel_y,
                    )
                    if osc_client:
                        osc_client.send_message("/captcha/cal/ack", [idx])
                    break  # move to next corner

    return True


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    settings = load_settings(args.config)

    # ---- camera ----
    cam_cfg = settings.get("camera", {})
    if args.mock:
        camera = MockCamera(
            width=cam_cfg.get("width", 640),
            height=cam_cfg.get("height", 400),
            fps=cam_cfg.get("framerate", 30),
        )
        log.info("Using mock camera")
    else:
        camera = OrbbecCamera(
            serial=cam_cfg.get("serial") or None,
            width=cam_cfg.get("width", 640),
            height=cam_cfg.get("height", 400),
            fps=cam_cfg.get("framerate", 30),
        )
        log.info("Using Orbbec camera serial=%s", cam_cfg.get("serial", "(any)"))

    # ---- touch detector ----
    detector = TouchDetector()
    det_cfg = settings.get("detection", {})
    detector.detection_config.touch_threshold_mm = det_cfg.get("touch_threshold_mm", 25)
    detector.detection_config.min_touch_pixels = det_cfg.get("min_touch_pixels", 30)
    detector.detection_config.max_touch_pixels = det_cfg.get("max_touch_pixels", 8000)

    cal_cfg = settings.get("calibration", {})
    bg_frames = cal_cfg.get("background_frames", 90)
    cal_file = Path(args.config).parent / cal_cfg.get("calibration_file", "calibration.json")
    corner_inset = cal_cfg.get("corner_inset", 0.05)

    # ---- grid tracker ----
    grid_cfg = settings.get("grid", {})
    tracker = GridTouchTracker(
        cols=grid_cfg.get("cols", 4),
        rows=grid_cfg.get("rows", 4),
        confirm_frames=settings.get("tracker", {}).get("confirm_frames", 3),
        release_frames=settings.get("tracker", {}).get("release_frames", 8),
    )
    log.info("Grid: %dx%d  confirm=%d  release=%d",
             tracker.cols, tracker.rows,
             tracker.confirm_frames, tracker.release_frames)

    # ---- OSC ----
    osc_client = None
    osc_cfg = settings.get("osc", {})
    if not args.no_osc:
        osc_client = make_osc_client(
            osc_cfg.get("target_ip", "127.0.0.1"),
            osc_cfg.get("target_port", 9001),
        )
        log.info("OSC → %s:%d", osc_cfg.get("target_ip"), osc_cfg.get("target_port"))

        # Mutable flags/refs shared with OSC callbacks.
        _recalibrate_flag = [False]

        def _on_grid_size(_addr, cols, rows):
            log.info("OSC: grid_size → %dx%d", cols, rows)
            tracker.resize(int(cols), int(rows))

        def _on_recalibrate(_addr):
            log.info("OSC: recalibrate requested")
            _recalibrate_flag[0] = True

        start_osc_server(
            osc_cfg.get("listen_port", 9002),
            _on_grid_size,
            _on_recalibrate,
        )
    else:
        _recalibrate_flag = [False]
        log.info("OSC disabled (--no-osc)")

    # ---- calibration ----
    calibration: ScreenCalibration | None = None
    need_corner_cal = args.recalibrate or args.mock

    if not need_corner_cal and cal_file.exists():
        try:
            calibration = ScreenCalibration.load(cal_file)
            log.info("Loaded calibration from %s", cal_file)
        except Exception as exc:
            log.warning("Could not load calibration (%s) — will recalibrate", exc)
            calibration = None

    if calibration is None:
        calibration = ScreenCalibration(corner_inset=corner_inset)
        if not args.mock:
            need_corner_cal = True  # real camera always needs corner cal if not loaded

    # In mock mode, use a default identity homography that maps the full camera
    # frame to the full screen so testing works without physical calibration.
    if args.mock and not calibration.is_complete:
        calibration = _make_mock_calibration(
            cam_cfg.get("width", 640),
            cam_cfg.get("height", 400),
            corner_inset,
        )
        log.info("Mock mode: using default full-frame homography")

    # ---- visualizer ----
    if not args.no_visualizer:
        from visualizer import broadcast as _broadcast_ws, start_server
        start_server(host="0.0.0.0", port=args.visualizer_port)
    else:
        def _broadcast_ws(_state):
            pass

    # Broadcast helper — builds the full state dict and pushes it to browsers.
    # Captured variables (calibration, tracker) are always the latest assignment
    # because Python closures capture by reference.
    cam_dims = [cam_cfg.get("width", 640), cam_cfg.get("height", 400)]
    bg_frames_captured = [0]

    def _broadcast(app_state_val: str, touches=None):
        if touches is None:
            touches = []
        corner_cal_data = None
        screen_touches: list[dict] = []
        if app_state_val == AppState.CORNER_CALIBRATION.value:
            corner_cal_data = {
                "corners_recorded": calibration.corners_recorded,
                "next_corner_name": calibration.next_corner_name,
                "next_corner_uv": (list(calibration.next_corner_uv)
                                   if calibration.next_corner_uv else None),
                "corner_uvs":     [list(uv) for uv in calibration.corner_uvs],
                "recorded_pixels": [list(p) for p in calibration.recorded_pixels],
            }
        elif app_state_val == AppState.RUNNING.value and calibration.is_complete:
            for touch in touches:
                uv_result = calibration.to_uv(touch.pixel_x, touch.pixel_y)
                if uv_result:
                    screen_touches.append({"u": uv_result[0], "v": uv_result[1]})
        _broadcast_ws({
            "frame":            frame_count,
            "app_state":        app_state_val,
            "bg_cal_progress":  min(bg_frames_captured[0] / max(bg_frames, 1), 1.0),
            "camera":           {"width": cam_dims[0], "height": cam_dims[1]},
            "corner_cal":       corner_cal_data,
            "raw_touches":      [{"px": t.pixel_x, "py": t.pixel_y,
                                   "pixel_count": t.pixel_count} for t in touches],
            "screen_touches":   screen_touches,
            "grid": {
                "cols":      tracker.cols,
                "rows":      tracker.rows,
                "confirmed": [[c, r] for c, r in tracker.confirmed_cells()],
            },
        })

    # ---- graceful shutdown ----
    _running = [True]

    def _stop(sig, frame):
        log.info("Shutting down…")
        _running[0] = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    # ---- main camera loop ----
    app_state = AppState.BACKGROUND_CALIBRATION
    frame_count = 0
    t_last_log = time.monotonic()

    with camera:
        frame_iter = camera.frames()

        for frame in frame_iter:
            if not _running[0]:
                break

            # === BACKGROUND CALIBRATION ===
            if app_state == AppState.BACKGROUND_CALIBRATION:
                if detector.state == CalibrationState.NOT_CALIBRATED:
                    cam_dims[0] = frame.width
                    cam_dims[1] = frame.height
                    detector.begin_calibration(bg_frames, frame.width, frame.height)
                    log.info("Background calibration started (%d frames)…", bg_frames)

                detector.push_calibration_frame(frame)
                bg_frames_captured[0] += 1
                _broadcast(AppState.BACKGROUND_CALIBRATION.value)

                if detector.state == CalibrationState.CALIBRATED:
                    log.info("Background calibration complete")
                    if need_corner_cal:
                        app_state = AppState.CORNER_CALIBRATION
                    else:
                        app_state = AppState.RUNNING
                        log.info("Running")
                continue

            # === CORNER CALIBRATION ===
            if app_state == AppState.CORNER_CALIBRATION:
                success = run_corner_calibration(
                    detector, calibration, frame_iter, osc_client, _running,
                    broadcast_fn=lambda touches: _broadcast(
                        AppState.CORNER_CALIBRATION.value, touches
                    ),
                )
                if not success:
                    break
                calibration.save(cal_file)
                log.info("Calibration saved to %s", cal_file)
                if osc_client:
                    osc_client.send_message("/captcha/cal/done", [])
                app_state = AppState.RUNNING
                log.info("Running")
                continue

            # === RUNNING ===
            if _recalibrate_flag[0]:
                _recalibrate_flag[0] = False
                calibration = ScreenCalibration(corner_inset=corner_inset)
                app_state = AppState.CORNER_CALIBRATION
                log.info("Recalibration triggered via OSC")
                continue

            touches = detector.detect(frame)

            # Map touches to grid cells via homography.
            active_cells: set[tuple[int, int]] = set()
            for touch in touches:
                uv = calibration.to_uv(touch.pixel_x, touch.pixel_y)
                if uv is None:
                    continue
                u, v = uv
                col = min(int(u * tracker.cols), tracker.cols - 1)
                row = min(int(v * tracker.rows), tracker.rows - 1)
                active_cells.add((col, row))

            events = tracker.update(active_cells)
            _broadcast(AppState.RUNNING.value, touches)

            if osc_client:
                for ev in events:
                    addr = "/captcha/touch/down" if ev.type == EventType.DOWN else "/captcha/touch/up"
                    osc_client.send_message(addr, [ev.col, ev.row])
                    log.debug("OSC %s %d %d", addr, ev.col, ev.row)

                # Full grid state every frame (cols, rows, cell0, cell1, ...).
                confirmed = tracker.confirmed_cells()
                state_args = [tracker.cols, tracker.rows] + [
                    int((col, row) in confirmed)
                    for row in range(tracker.rows)
                    for col in range(tracker.cols)
                ]
                osc_client.send_message("/captcha/state", state_args)

            frame_count += 1

            # Periodic log.
            now = time.monotonic()
            if now - t_last_log >= 5.0:
                log.info(
                    "frame %d | touches=%d | confirmed_cells=%d | grid=%dx%d",
                    frame_count, len(touches), len(tracker.confirmed_cells()),
                    tracker.cols, tracker.rows,
                )
                t_last_log = now


# ---------------------------------------------------------------------------
# Mock calibration helper
# ---------------------------------------------------------------------------

def _make_mock_calibration(width: int, height: int, inset: float) -> ScreenCalibration:
    """
    Build a calibration that maps the full camera frame to the full screen.
    The 4 'corners' are placed at the inset positions within the camera frame.
    """
    cal = ScreenCalibration(corner_inset=inset)
    i_x = width * inset
    i_y = height * inset
    corners_px = [
        (i_x,         i_y        ),  # top-left
        (width - i_x, i_y        ),  # top-right
        (width - i_x, height - i_y),  # bottom-right
        (i_x,         height - i_y),  # bottom-left
    ]
    for px, py in corners_px:
        cal.add_corner(px, py)
    return cal


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="FundingCAPTCHA touch-screen detector")
    ap.add_argument("--config", default="settings.json", help="Path to settings JSON")
    ap.add_argument("--mock", action="store_true", help="Use mock camera (no hardware)")
    ap.add_argument("--recalibrate", action="store_true",
                    help="Force re-run of corner calibration even if a saved file exists")
    ap.add_argument("--no-osc", action="store_true", help="Disable OSC output/input")
    ap.add_argument("--no-visualizer", action="store_true", help="Disable browser visualizer")
    ap.add_argument("--visualizer-port", type=int, default=8766, help="Visualizer HTTP port")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    run(args)


if __name__ == "__main__":
    main()
