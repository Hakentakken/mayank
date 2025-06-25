import cv2
import tkinter as tk
from PIL import Image, ImageTk
from threading import Thread
from calib_module import auto_calibrate
from tracker import ShotTracker

class ShootingApp:
    def __init__(self, root, M, camera_port):
        self.root = root
        self.root.title("🔫 Target Shooting Tracker")
        self.root.geometry("1100x650")
        self.root.configure(bg="#222831")

        # Header Frame
        self.header_frame = tk.Frame(root, bg="#393e46")
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        self.title_label = tk.Label(
            self.header_frame, text="🔫 Target Shooting Tracker",
            font=("Arial", 22, "bold"), fg="#ffd369", bg="#393e46"
        )
        self.title_label.pack(side=tk.LEFT, padx=20, pady=10)

        self.score_label = tk.Label(
            self.header_frame, text="Total Score: 0",
            font=("Arial", 18, "bold"), fg="#00adb5", bg="#393e46"
        )
        self.score_label.pack(side=tk.RIGHT, padx=20)

        # Camera Port Selection
        self.camera_port_var = tk.IntVar(value=0)
        self.camera_port_menu = tk.OptionMenu(
            self.header_frame, self.camera_port_var, *range(5)
        )
        self.camera_port_menu.config(font=("Arial", 12), bg="#222831", fg="#ffd369", highlightbackground="#393e46")
        self.camera_port_menu.pack(side=tk.RIGHT, padx=10)
        self.camera_label = tk.Label(
            self.header_frame, text="Camera Port:", font=("Arial", 12), fg="#ffd369", bg="#393e46"
        )
        self.camera_label.pack(side=tk.RIGHT, padx=(0, 2))

        # Main Content Frame
        self.content_frame = tk.Frame(root, bg="#222831")
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas for video
        self.canvas = tk.Canvas(self.content_frame, width=640, height=480, bg='black', highlightthickness=2, highlightbackground="#393e46")
        self.canvas.grid(row=0, column=0, rowspan=3, padx=20, pady=20)

        # Info/Sidebar Frame
        self.info_frame = tk.Frame(self.content_frame, bg="#222831")
        self.info_frame.grid(row=0, column=1, sticky="n", padx=10, pady=20)

        self.shot_list_label = tk.Label(
            self.info_frame, text="Shot History",
            font=("Arial", 16, "bold"), fg="#ffd369", bg="#222831"
        )
        self.shot_list_label.pack(pady=(0, 10))

        self.shot_listbox = tk.Listbox(
            self.info_frame, font=("Courier", 12), width=25, height=20,
            bg="#393e46", fg="#eeeeee", selectbackground="#00adb5"
        )
        self.shot_listbox.pack(pady=(0, 10))

        # Scoreboard
        self.stats_frame = tk.Frame(self.info_frame, bg="#222831")
        self.stats_frame.pack(pady=10, fill=tk.X)

        self.shots_label = tk.Label(
            self.stats_frame, text="Shots: 0",
            font=("Arial", 14), fg="#00adb5", bg="#222831"
        )
        self.shots_label.pack(anchor="w")

        self.clear_btn = tk.Button(
            self.info_frame, text="Clear Shots", font=("Arial", 12, "bold"),
            bg="#00adb5", fg="#222831", activebackground="#ffd369",
            command=self.clear_shots
        )
        self.clear_btn.pack(pady=10, fill=tk.X)

        self.M = M
        self.tracker = ShotTracker()
        self.prev_frame = None
        self.bg_img = cv2.imread("target.jpg")
        self.cap = None
        self.running = False
        self.camera_port = camera_port

        self.start_tracking()

        self.switch_cam_btn = tk.Button(
            self.header_frame, text="Switch Camera", font=("Arial", 12, "bold"),
            bg="#ffd369", fg="#222831", activebackground="#00adb5",
            command=self.switch_camera
        )
        self.switch_cam_btn.pack(side=tk.RIGHT, padx=10)

    def start_tracking(self):
        self.cap = cv2.VideoCapture(self.camera_port)
        # Enable auto focus if supported
        if self.cap is not None and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        self.running = True
        Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Warp the live camera frame using the calibration matrix
            warped = cv2.warpPerspective(frame, self.M, (self.bg_img.shape[1], self.bg_img.shape[0]))

            shot = None
            if self.prev_frame is not None:
                shot = self.tracker.detect_shot(self.prev_frame, warped)

            # Use the live warped frame as the background for drawing shots
            result = warped.copy()
            result = self.tracker.draw_shots(result)

            if shot:
                self.update_score_list()

            # Convert for tkinter
            img = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img

            self.prev_frame = warped.copy()

            if cv2.waitKey(30) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def clear_shots(self):
        self.tracker.shots.clear()
        self.update_score_list()
        self.canvas.delete("all")
        self.prev_frame = None

    def update_score_list(self):
        self.shot_listbox.delete(0, tk.END)
        scores = self.tracker.get_score_list()
        for i, score in enumerate(scores, start=1):
            self.shot_listbox.insert(tk.END, f"Shot {i}: {score} pts")
        total_score = sum(scores)
        self.score_label.config(text=f"Total Score: {total_score}")
        self.shots_label.config(text=f"Shots: {len(scores)}")

    def switch_camera(self):
        # Stop current camera loop if running
        self.running = False
        if self.cap is not None:
            self.cap.release()
        self.prev_frame = None
        self.canvas.delete("all")
        self.start_tracking()

if __name__ == '__main__':
    # Do calibration and camera selection BEFORE showing main window
    M, camera_port = auto_calibrate(return_port=True)
    if M is None or camera_port is None:
        print("Calibration or camera selection failed. Exiting.")
        exit(1)
    root = tk.Tk()
    app = ShootingApp(root, M, camera_port)
    root.mainloop()
