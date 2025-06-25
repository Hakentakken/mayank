import cv2
import numpy as np

ring_scores = [(10, 10), (30, 9), (50, 8), (70, 7), (90, 6), (110, 5), (130, 4), (150, 3), (170, 2), (190, 1)]

class ShotTracker:
    def __init__(self, target_center=(320, 240)):
        self.shots = []
        self.target_center = target_center
        self.pending_shot = None
        self.pending_count = 0

    def detect_shot(self, prev, curr):
        gray1 = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)

        # Use a lower threshold to catch subtle tears
        _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)

        # Optional: Use Canny edge detection to enhance torn edges
        edges = cv2.Canny(diff, 30, 150)
        thresh = cv2.bitwise_or(thresh, edges)

        # Morphological operations to reduce noise and close holes
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Calculate total area of all contours
        total_area = sum(cv2.contourArea(cnt) for cnt in contours)
        if total_area > 400:
            return None

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 20 < area < 200:  # Bullet holes or tears are small but not too tiny
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0:
                    continue
                circularity = 4 * np.pi * (area / (perimeter * perimeter))
                if 0.4 < circularity < 1.3:  # Accept slightly irregular circles (torn holes)
                    x, y, w, h = cv2.boundingRect(cnt)
                    cx, cy = x + w // 2, y + h // 2
                    if not self.is_duplicate((cx, cy)):
                        score = self.get_score((cx, cy))
                        self.shots.append((cx, cy, score))
                        print(f"🎯 Shot at ({cx}, {cy}) | Score: {score}")
                        return (cx, cy, score)
        return None

    def is_duplicate(self, pt):
        for shot in self.shots:
            if abs(shot[0] - pt[0]) < 10 and abs(shot[1] - pt[1]) < 10:
                return True
        return False

    def get_score(self, pt):
        dx, dy = pt[0] - self.target_center[0], pt[1] - self.target_center[1]
        distance = np.sqrt(dx ** 2 + dy ** 2)
        for radius, score in ring_scores:
            if distance <= radius:
                return score
        return 0

    def draw_shots(self, frame):
        for x, y, score in self.shots:
            cv2.circle(frame, (x, y), 6, (0, 0, 255), 2)
            cv2.putText(frame, str(score), (x+8, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        return frame

    def get_score_list(self):
        return [s[2] for s in self.shots]
