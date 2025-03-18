import numpy as np

class NoddingDetector:
    def __init__(self, nod_threshold=15, moving_avg_window=10):
        self.nod_threshold = nod_threshold
        self.moving_avg_window = moving_avg_window
        self.y_positions = []

    def detect(self, landmarks):
        """머리의 Y축 변화를 감지하여 졸음 끄덕임 여부 판별"""
        nose_y = landmarks[33][1]  # 코 끝 좌표 (고개 움직임 기준)
        
        self.y_positions.append(nose_y)
        if len(self.y_positions) > self.moving_avg_window:
            self.y_positions.pop(0)

        if len(self.y_positions) < self.moving_avg_window:
            return "Normal"

        y_movement = self.y_positions[-1] - self.y_positions[0]

        if abs(y_movement) > self.nod_threshold:
            return "Nodding"
        return "Normal"
