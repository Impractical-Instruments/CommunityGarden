"""
captcha_touch.py
4x4 grid touch detection for Funding CAPTCHA
Hardware: Orbbec Gemini 336L + Raspberry Pi 5
Stack: pyorbbecsdk, OpenCV, numpy, pygame (OSC output via python-osc)

Install deps:
    pip install opencv-python numpy python-osc
    # pyorbbecsdk: follow https://orbbec.github.io/pyorbbecsdk/
"""

import cv2
import numpy as np
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Tuple
from pythonosc import udp_client  # pip install python-osc

# --- pyorbbecsdk imports ---
from pyorbbecsdk import (
    Pipeline, Config, OBSensorType, OBFormat,
    FrameSet, DepthFrame
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GRID_COLS = 4
GRID_ROWS = 4

# Depth thresholds (mm from surface)
# Finger must be closer than ENTER_MM to start a touch,
# and farther than EXIT_MM to release. Schmitt trigger.
ENTER_MM = 35
EXIT_MM  = 55

# Temporal debounce
FRAMES_TO_ENTER = 4   # consecutive frames to confirm touch
FRAMES_TO_EXIT  = 3   # consecutive frames to confirm release

# Background model
BG_FRAME_COUNT    = 30   # frames to average for initial background
BG_UPDATE_ALPHA   = 0.002 # slow drift correction per frame (0=frozen, 1=instant)

# Morphological cleanup kernel size (pixels)
MORPH_KERNEL_SIZE = 5

# Minimum blob area to count as a touch (pixels^2)
MIN_BLOB_AREA = 150

# Camera depth stream resolution
DEPTH_WIDTH  = 640
DEPTH_HEIGHT = 480

# Projection surface ROI in depth camera pixel space.
# Set these after running calibration (see calibrate() below).
# Format: (x, y, width, height) in depth frame pixels.
# Default covers full frame — narrow this after calibration.
ROI = (0, 0, DEPTH_WIDTH, DEPTH_HEIGHT)

# OSC output
OSC_HOST = "127.0.0.1"
OSC_PORT = 9000

# ---------------------------------------------------------------------------
# Touch state machine per cell
# ---------------------------------------------------------------------------

@dataclass
class CellState:
    row: int
    col: int
    touch_active: bool = False
    enter_count:  int  = 0
    exit_count:   int  = 0

# ---------------------------------------------------------------------------
# Detector class
# ---------------------------------------------------------------------------

class GridTouchDetector:

    def __init__(self, osc_client=None):
        self.osc   = osc_client
        self.cells = [
            [CellState(r, c) for c in range(GRID_COLS)]
            for r in range(GRID_ROWS)
        ]

        self.background: Optional[np.ndarray] = None
        self.bg_ready   = False
        self.bg_frames  = []

        self._pipeline: Optional[Pipeline] = None
        self._running   = False
        self._lock      = threading.Lock()
        self.latest_mask: Optional[np.ndarray] = None  # for debug display

    # ------------------------------------------------------------------
    # Camera setup
    # ------------------------------------------------------------------

    def start(self):
        self._pipeline = Pipeline()
        config = Config()
        config.enable_stream(OBSensorType.DEPTH_SENSOR, DEPTH_WIDTH, DEPTH_HEIGHT, OBFormat.Y16, 30)
        self._pipeline.start(config)
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("Touch detector started.")

    def stop(self):
        self._running = False
        if self._pipeline:
            self._pipeline.stop()
        print("Touch detector stopped.")

    # ------------------------------------------------------------------
    # Main loop (runs in background thread)
    # ------------------------------------------------------------------

    def _loop(self):
        morph_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE)
        )

        while self._running:
            frameset: FrameSet = self._pipeline.wait_for_frames(100)
            if frameset is None:
                continue

            depth_frame: DepthFrame = frameset.get_depth_frame()
            if depth_frame is None:
                continue

            # Convert to numpy mm array
            raw = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
            raw = raw.reshape((DEPTH_HEIGHT, DEPTH_WIDTH)).astype(np.float32)

            # Apply scale factor to get millimetres
            scale = depth_frame.get_depth_scale()
            depth_mm = raw * scale

            # Crop to ROI
            x, y, w, h = ROI
            roi_depth = depth_mm[y:y+h, x:x+w]

            # --- Background model ---
            if not self.bg_ready:
                self._accumulate_background(roi_depth)
                continue

            # Slow background drift update (handles slow scene changes)
            self.background = (
                self.background * (1 - BG_UPDATE_ALPHA)
                + roi_depth      * BG_UPDATE_ALPHA
            )

            # --- Per-pixel threshold ---
            # Positive diff = object closer than background
            diff = self.background - roi_depth

            # Zero out pixels where background has no data
            valid = (self.background > 0) & (roi_depth > 0)
            diff[~valid] = 0

            # Touch band: between ENTER and EXIT thresholds
            # We use EXIT_MM as the outer bound for the mask —
            # state machine handles hysteresis
            raw_mask = (diff > 0) & (diff < EXIT_MM)
            raw_mask = raw_mask.astype(np.uint8) * 255

            # Morphological open: kills noise, preserves blobs
            clean_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, morph_kernel)

            with self._lock:
                self.latest_mask = clean_mask.copy()

            # --- Grid cell analysis ---
            cell_h = h / GRID_ROWS
            cell_w = w / GRID_COLS

            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    y0 = int(r * cell_h)
                    y1 = int((r + 1) * cell_h)
                    x0 = int(c * cell_w)
                    x1 = int((c + 1) * cell_w)

                    cell_mask = clean_mask[y0:y1, x0:x1]
                    cell_diff = diff[y0:y1, x0:x1]

                    # Check if any blob in this cell is large enough
                    # AND close enough (within ENTER_MM) to qualify
                    enter_zone = ((cell_diff > 0) & (cell_diff < ENTER_MM)).astype(np.uint8) * 255
                    enter_area = int(np.sum(enter_zone > 0))

                    touching = enter_area >= MIN_BLOB_AREA
                    self._update_cell(self.cells[r][c], touching)

    def _accumulate_background(self, depth_roi: np.ndarray):
        """Collect BG_FRAME_COUNT frames and average them."""
        # Only use pixels with valid depth readings
        valid = depth_roi > 0
        if np.sum(valid) < (depth_roi.size * 0.5):
            return  # too many invalid pixels, skip frame

        self.bg_frames.append(depth_roi.copy())

        if len(self.bg_frames) == 1:
            print(f"Collecting background ({BG_FRAME_COUNT} frames)...")

        if len(self.bg_frames) >= BG_FRAME_COUNT:
            stack = np.stack(self.bg_frames, axis=0)
            # Median is more robust than mean against transient occlusions
            self.background = np.median(stack, axis=0).astype(np.float32)
            self.bg_ready   = True
            self.bg_frames  = []
            print("Background model ready.")

    # ------------------------------------------------------------------
    # Touch state machine
    # ------------------------------------------------------------------

    def _update_cell(self, cell: CellState, touching: bool):
        if not cell.touch_active:
            if touching:
                cell.enter_count += 1
                cell.exit_count   = 0
                if cell.enter_count >= FRAMES_TO_ENTER:
                    cell.touch_active = True
                    cell.enter_count  = 0
                    self._fire_event(cell, "DOWN")
            else:
                cell.enter_count = 0
        else:
            if not touching:
                cell.exit_count  += 1
                cell.enter_count  = 0
                if cell.exit_count >= FRAMES_TO_EXIT:
                    cell.touch_active = False
                    cell.exit_count   = 0
                    self._fire_event(cell, "UP")
            else:
                cell.exit_count = 0

    def _fire_event(self, cell: CellState, event: str):
        print(f"TOUCH_{event}  row={cell.row}  col={cell.col}")
        if self.osc:
            self.osc.send_message(
                f"/captcha/touch/{event.lower()}",
                [cell.row, cell.col]
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_touch_state(self) -> list[list[bool]]:
        """Returns 4x4 grid of current touch active states."""
        return [[self.cells[r][c].touch_active for c in range(GRID_COLS)]
                for r in range(GRID_ROWS)]

    def recalibrate_background(self):
        """Call this to force a fresh background capture."""
        self.bg_ready  = False
        self.bg_frames = []
        print("Background recalibration triggered.")

# ---------------------------------------------------------------------------
# Calibration helper
# ---------------------------------------------------------------------------

def calibrate():
    """
    Interactive calibration to set the ROI.

    Run this standalone to find the depth camera pixel coordinates
    of your projection surface corners. Prints ROI values to paste
    into the ROI constant above.

    Usage:
        python captcha_touch.py --calibrate
    """
    pipeline = Pipeline()
    config   = Config()
    config.enable_stream(OBSensorType.DEPTH_SENSOR, DEPTH_WIDTH, DEPTH_HEIGHT, OBFormat.Y16, 30)
    pipeline.start(config)

    print("CALIBRATION MODE")
    print("Click the four corners of the projected surface.")
    print("Press Q when done, R to reset clicks.")

    clicks = []

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(clicks) < 4:
            clicks.append((x, y))
            print(f"  Corner {len(clicks)}: ({x}, {y})")

    cv2.namedWindow("Calibrate — depth")
    cv2.setMouseCallback("Calibrate — depth", on_click)

    while True:
        frameset = pipeline.wait_for_frames(100)
        if frameset is None:
            continue
        depth_frame = frameset.get_depth_frame()
        if depth_frame is None:
            continue

        raw = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
        raw = raw.reshape((DEPTH_HEIGHT, DEPTH_WIDTH))
        vis = cv2.normalize(raw, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        vis = cv2.applyColorMap(vis, cv2.COLORMAP_JET)

        for pt in clicks:
            cv2.circle(vis, pt, 6, (255, 255, 255), -1)

        cv2.imshow("Calibrate — depth", vis)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('r'):
            clicks.clear()
            print("Reset.")
        elif key == ord('q'):
            break

    pipeline.stop()
    cv2.destroyAllWindows()

    if len(clicks) == 4:
        xs = [p[0] for p in clicks]
        ys = [p[1] for p in clicks]
        x0, y0 = min(xs), min(ys)
        x1, y1 = max(xs), max(ys)
        print(f"\nPaste this into captcha_touch.py:")
        print(f"ROI = ({x0}, {y0}, {x1-x0}, {y1-y0})")
    else:
        print("Need 4 corners — run again.")

# ---------------------------------------------------------------------------
# Debug display (optional, runs in main thread alongside detector)
# ---------------------------------------------------------------------------

def debug_display(detector: GridTouchDetector):
    """
    Shows live depth mask and grid touch state in a pygame window.
    Useful during tuning. Remove in production.
    """
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Touch Debug")
    font   = pygame.font.SysFont("monospace", 24)
    clock  = pygame.time.Clock()

    CELL_W = 800 // GRID_COLS
    CELL_H = 600 // GRID_ROWS

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                detector.recalibrate_background()

        screen.fill((20, 20, 20))

        # Draw grid cells
        state = detector.get_touch_state()
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                color  = (0, 200, 80) if state[r][c] else (50, 50, 50)
                border = (100, 100, 100)
                rect   = pygame.Rect(c * CELL_W, r * CELL_H, CELL_W, CELL_H)
                pygame.draw.rect(screen, color,  rect)
                pygame.draw.rect(screen, border, rect, 2)
                label = font.render(f"{r},{c}", True, (200, 200, 200))
                screen.blit(label, (rect.x + 8, rect.y + 8))

        # Status
        status = "BG READY" if detector.bg_ready else "COLLECTING BG..."
        txt    = font.render(status, True, (255, 200, 0))
        screen.blit(txt, (10, 570))

        hint = font.render("R = recalibrate background", True, (120, 120, 120))
        screen.blit(hint, (400, 570))

        pygame.display.flip()
        clock.tick(30)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if "--calibrate" in sys.argv:
        calibrate()
        sys.exit(0)

    osc = udp_client.SimpleUDPClient(OSC_HOST, OSC_PORT)
    detector = GridTouchDetector(osc_client=osc)
    detector.start()

    try:
        # Run debug display in main thread (remove in production,
        # or replace with your pygame show control loop)
        debug_display(detector)
    except KeyboardInterrupt:
        pass
    finally:
        detector.stop()