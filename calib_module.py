import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk

def list_available_cameras(max_ports=10):
    available = []
    for i in range(max_ports):
        cap = cv2.VideoCapture(i)
        if cap is not None and cap.isOpened():
            available.append(i)
            cap.release()
    return available

def select_camera_gui(available_ports):
    selected = {'port': None}
    def on_select(event=None):
        selected['port'] = int(combo.get())
        root.destroy()
    root = tk.Tk()
    root.title("Select Camera")
    tk.Label(root, text="Select Camera Port:", font=("Arial", 14)).pack(padx=10, pady=10)
    combo = ttk.Combobox(root, values=available_ports, font=("Arial", 12), state="readonly")
    combo.pack(padx=10, pady=10)
    combo.current(0)
    btn = tk.Button(root, text="OK", font=("Arial", 12), command=on_select)
    btn.pack(pady=10)
    root.bind('<Return>', on_select)
    root.mainloop()
    return selected['port']

def auto_calibrate(target_image_path="target.jpg", max_ports=10, return_port=False):
    available_ports = list_available_cameras(max_ports)
    if not available_ports:
        print("No cameras found!")
        return (None, None) if return_port else None
    cam_port = select_camera_gui(available_ports)
    if cam_port is None:
        print("No camera selected.")
        return (None, None) if return_port else None

    cap = cv2.VideoCapture(cam_port)
    template = cv2.imread(target_image_path, 0)
    h, w = template.shape[:2]

    print("🔍 Auto-calibrating using template... Please hold target steady.")
    print("Press 'y' to confirm, 'n' to retry, 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)

        preview = frame.copy()
        cv2.rectangle(preview, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(preview, f"Target detected - Press Y to confirm | Cam: {cam_port}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.imshow("Confirm Target - Press Y/N/Q", preview)

        key = cv2.waitKey(1)
        if key == ord('y'):
            pts1 = np.float32([
                [top_left[0], top_left[1]],               # TL
                [top_left[0]+w, top_left[1]],             # TR
                [top_left[0]+w, top_left[1]+h],           # BR
                [top_left[0], top_left[1]+h]              # BL
            ])
            pts2 = np.float32([
                [0, 0], [w, 0], [w, h], [0, h]
            ])
            M = cv2.getPerspectiveTransform(pts1, pts2)
            print("✅ Auto calibration successful")
            cap.release()
            cv2.destroyAllWindows()
            return (M, cam_port) if return_port else M

        elif key == ord('n'):
            print("🔁 Retrying...")
            continue

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return (None, None) if return_port else None
