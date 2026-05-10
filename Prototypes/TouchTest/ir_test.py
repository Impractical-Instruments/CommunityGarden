#!/usr/bin/env python3
"""
IR stream viewer for Orbbec Gemini 336L.

Shows the left IR sensor image normalised and CLAHE-enhanced.
Useful for checking IR interference from laser projectors.

Keys: Q — quit   C — toggle CLAHE   R — toggle raw (no normalise)
"""

import argparse
import sys

import cv2
import numpy as np
from pyorbbecsdk import Config, Context, OBFormat, OBSensorType, Pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--serial", default=None, help="Camera serial (auto-detect if omitted)")
ap.add_argument("--sensor", default="left", choices=["left", "right"],
                help="Which IR sensor to use (default: left)")
ap.add_argument("--list-profiles", action="store_true",
                help="Print available IR profiles and exit")
args = ap.parse_args()

sensor_type = OBSensorType.LEFT_IR_SENSOR if args.sensor == "left" else OBSensorType.RIGHT_IR_SENSOR

# Build pipeline
if args.serial:
    ctx     = Context()
    device  = ctx.query_devices().get_device_by_serial_number(args.serial)
    pipeline = Pipeline(device)
else:
    pipeline = Pipeline()

# Enumerate profiles
profile_list = pipeline.get_stream_profile_list(sensor_type)
count = profile_list.get_count()
print(f"IR ({args.sensor}) — {count} profiles available:")
for i in range(count):
    p  = profile_list.get_stream_profile_by_index(i)
    vp = p.as_video_stream_profile()
    print(f"  [{i}] {vp.get_width()}x{vp.get_height()}  {vp.get_format()}  @{vp.get_fps()}fps")

if args.list_profiles:
    sys.exit(0)

profile = profile_list.get_default_video_stream_profile()
vp = profile.as_video_stream_profile()
print(f"\nUsing: {vp.get_width()}x{vp.get_height()}  {vp.get_format()}  @{vp.get_fps()}fps")

config = Config()
config.enable_stream(profile)
pipeline.start(config)
print("Press Q to quit, C to toggle CLAHE, R to toggle raw mode.")

clahe    = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
use_clahe = True
use_norm  = True

try:
    while True:
        frameset = pipeline.wait_for_frames(100)
        if not frameset:
            continue
        ir_frame = frameset.get_ir_frame()
        if ir_frame is None:
            continue

        fmt = ir_frame.get_format()
        raw = bytes(ir_frame.get_data())
        w   = ir_frame.get_width()
        h   = ir_frame.get_height()

        if fmt == OBFormat.Y16:
            arr = np.frombuffer(raw, dtype=np.uint16).reshape(h, w)
            if use_norm:
                img = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            else:
                img = (arr >> 8).astype(np.uint8)
        else:
            # Y8 / GRAY
            arr = np.frombuffer(raw, dtype=np.uint8).reshape(h, w)
            img = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX) if use_norm else arr.copy()

        if use_clahe:
            img = clahe.apply(img)

        cv2.imshow("IR stream  (Q=quit  C=clahe  R=raw)", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            use_clahe = not use_clahe
            print(f"CLAHE: {'on' if use_clahe else 'off'}")
        elif key == ord('r'):
            use_norm = not use_norm
            print(f"Normalise: {'on' if use_norm else 'off'}")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
