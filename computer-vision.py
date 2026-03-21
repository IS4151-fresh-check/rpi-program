import cv2
from ultralytics import YOLO

# 1. Load your 99% accurate model
model = YOLO('banana_cv_model.pt')

# 2. Connect to the camera (0 is usually the default USB or Ribbon cam)
cap = cv2.VideoCapture(0)

print("Starting Banana Classifier... Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 3. Run inference (stream=True is faster for video)
    results = model(frame, stream=True)

    for r in results:
        # Get the top prediction name and confidence
        probs = r.probs
        class_id = probs.top1
        conf = probs.top1conf.item()
        label = r.names[class_id]

        # 4. Display the result on the screen
        text = f"{label} ({conf:.2%})"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 255, 0), 2, cv2.LINE_AA)

    # Show the camera feed
    #cv2.imshow('Banana Scanner', frame)

    # Break loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
