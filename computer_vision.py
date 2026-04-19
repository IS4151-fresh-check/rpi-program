import cv2
from ultralytics import YOLO
import base64
import time
import numpy as np
from picamera2 import Picamera2

# Global variable for the camera object
picam2 = None

# 1. Load your model
model = YOLO('banana_cv_model.pt')

def init_camera():
    global picam2
    if picam2 is None:
        try:
            picam2 = Picamera2()
            # Configure for 640x480 RGB (YOLO's native format)
            config = picam2.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            picam2.configure(config)
            picam2.start()
            
            print("Picamera2 started successfully. Resolution: 640x480")
            # Give the sensor a moment to adjust exposure/white balance
            time.sleep(2)
        except Exception as e:
            print(f"CRITICAL: Picamera2 failed to open: {e}")

def read_camera():
    global picam2
    print("Reading camera")
    
    if picam2 is None:
        return {"cvStage": None, "cvConfidence": 0, "imageBase64": None}

    try:
        # 1. Capture direct to numpy array (Much faster/stable than GStreamer)
        frame_rgb = picam2.capture_array()
        
        # 3. Run Inference
        results = model(frame_rgb)
        r = results[0]
        probs = r.probs

        class_id = probs.top1
        conf = probs.top1conf.item()
        label = r.names[class_id]

        if label == "freshripe":
            label = "ripe"
        elif label == "freshunripe" or label == "unripe":
            label = "fresh"
        elif label == "freshoverripe":
            label = "overripe"
        elif label == "rotten":
            label = "spoiled"

        # 4. Save image for the UI (Resize for smaller Base64 payload)
        small_frame = cv2.resize(frame_rgb, (320, 240))
        _, buffer = cv2.imencode('.jpg', small_frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')

        return {
            "cvStage": label,
            "cvConfidence": round(conf, 4),
            "imageBase64": image_base64
        }

    except Exception as e:
        print(f"ERROR IN CAMERA PROCESSING: {e}")
        return {"cvStage": None, "cvConfidence": 0, "imageBase64": None}

def release_camera():
    global picam2
    if picam2 is not None:
        picam2.stop()
        picam2 = None
        print("Picamera2 released")