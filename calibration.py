import cv2
import numpy as np

clicked_points = []

def mouse_click(event, x, y, flags, param):
    global clicked_points
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_points.append((x, y))
        print(f"Point {len(clicked_points)}: {x}, {y}")

def calibrate_camera():
    global clicked_points
    cap = cv2.VideoCapture(0)
    print("🖱 Click on the 4 corners of the physical target (in clockwise order)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display = frame.copy()
        for i, pt in enumerate(clicked_points):
            cv2.circle(display, pt, 5, (0, 255, 0), -1)
            cv2.putText(display, str(i+1), (pt[0]+10, pt[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imshow("Click 4 Target Corners", display)
        cv2.setMouseCallback("Click 4 Target Corners", mouse_click)

        if len(clicked_points) == 4:
            print("✅ Got 4 points. Calibrating...")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("❌ Cancelled.")
            cap.release()
            cv2.destroyAllWindows()
            return None, None

    cap.release()
    cv2.destroyAllWindows()

    # Target image is 640x480, so we'll map to:
    virtual_target_points = np.array([
        [100, 100],
        [540, 100],
        [540, 380],
        [100, 380]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(np.array(clicked_points, dtype="float32"), virtual_target_points)
    return M, virtual_target_points
