import numpy as np

class NoddingDetector:
    def __init__(self, nod_threshold=15, moving_avg_window=10, tilt_threshold=10):
        self.nod_threshold = nod_threshold
        self.moving_avg_window = moving_avg_window
        self.tilt_threshold = tilt_threshold
        self.y_positions = []

    def detect(self, landmarks):
        """아래로 숙이는 Y 변화 + 기울임 방지"""
        # 1. 코 Y 좌표 추적 (끄덕임 감지)
        nose_y = landmarks[33][1]
        self.y_positions.append(nose_y)
        if len(self.y_positions) > self.moving_avg_window:
            self.y_positions.pop(0)

        if len(self.y_positions) < self.moving_avg_window:
            return "Normal"

        y_movement = self.y_positions[-1] - self.y_positions[0]

        # 2. 좌우 기울임 방지
        eye_tilt = abs(landmarks[36][1] - landmarks[45][1])
        if eye_tilt > self.tilt_threshold:
            return "Normal"

        # 3. 아래로 숙였을 때만 감지
        if y_movement > self.nod_threshold:
            return "Nodding"

        return "Normal"
