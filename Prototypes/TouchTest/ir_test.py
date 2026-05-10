import cv2
import numpy as np
from pyorbbecsdk import Pipeline, Config, OBSensorType, OBFormat

pipeline = Pipeline()
config = Config()
config.enable_stream(OBSensorType.IR_LEFT, 848, 480, OBFormat.Y8, 30)
pipeline.start(config)

try:
    while True:
        frames = pipeline.wait_for_frames(100)
        if not frames:
            continue
        ir_frame = frames.get_ir_frame()
        if ir_frame is None:
            continue
        data = np.frombuffer(bytes(ir_frame.get_data()), dtype=np.uint8)
        img = data.reshape((ir_frame.get_height(), ir_frame.get_width()))
        # Normalize for visibility — IR can be low contrast raw
        display = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
        cv2.imshow("IR", display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    pipeline.stop()
    cv2.destroyAllWindows()