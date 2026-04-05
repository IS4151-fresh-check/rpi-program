import cv2
from ultralytics import YOLO
import base64
import time

cap = None

def encode_to_base64(filepath):
    with open(filepath, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# 1. Load your 99% accurate model
model = YOLO('banana_cv_model.pt')

def init_camera():
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
        time.sleep(1) 
        print("Camera initialising")

# 2. Connect to the camera (0 is usually the default USB or Ribbon cam)
def read_camera():
    global cap
    init_camera()
    print("Reading camera")
    ret, frame = cap.read()
    if not ret:
        return {
            "cvStage": None,
            "cvConfidence": 0,
            "imageUrl": None
        }
    results = model(frame)
    r = results[0]
    probs = r.probs

    class_id = probs.top1
    conf = probs.top1conf.item()
    label = r.names[class_id]

    # --- Save image locally ---
    filename = "/home/pi/latest.jpg"
    frame = cv2.resize(frame, (320, 240))
    cv2.imwrite(filename, frame)

    try:
        image_base64 = encode_to_base64(filename)
    except Exception as e:
        print("Base64 encoding failed:", e)
        image_base64 = None

    return {
        "cvStage": label,
        "cvConfidence": round(conf, 4),
        "imageBase64": image_base64
    }

def release_camera():
    global cap
    if cap is not None and cap.isOpened():
        cap.release()
        cap = None
        print("Camera released")