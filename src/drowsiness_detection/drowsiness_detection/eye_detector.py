#!/usr/bin/env python3
import numpy as np
from scipy.spatial import distance as dist
import plotly.graph_objects as go


class EyeDetector:
    def __init__(self, logger, calibration_frames=180 ):
        self.logger = logger
        self.calibration_frames = calibration_frames
        self.ear_values = []
        self.eye_calibrated = False
        self.baseline_ear = 0
        self.eye_threshold = 0

    def detect(self, landmarks):
        def compute_EAR(eye):
            A = dist.euclidean(eye[1], eye[5])
            B = dist.euclidean(eye[2], eye[4])
            C = dist.euclidean(eye[0], eye[3])
            ear = (A + B) / (2.0 * C)
            return ear

        left_eye = landmarks[36:42]
        right_eye = landmarks[42:48]
        left_EAR = compute_EAR(left_eye)
        right_EAR = compute_EAR(right_eye)
        ear_avg = (left_EAR + right_EAR) / 2.0
        return ear_avg

    # -----------------------------
    #  시각화 함수
    # -----------------------------
    def plot_ear_threshold_graph(self):
        x_vals = list(range(len(self.ear_values)))

        fig = go.Figure()

        # EAR 값들 (초록색 점)
        fig.add_trace(go.Scatter(
            x=x_vals, y=self.ear_values, mode='markers', name='EAR 값',
            marker=dict(color='green', size=6)
        ))

        # Threshold 값 (빨간 수평선)
        fig.add_trace(go.Scatter(
            x=x_vals, y=[self.eye_threshold] * len(self.ear_values),
            mode='lines', name='Threshold',
            line=dict(color='red', dash='dash')
        ))

        fig.update_layout(
            title='EAR Calibration 결과 시각화',
            xaxis_title='프레임 인덱스',
            yaxis_title='EAR 값',
            template='plotly_white',
            height=500
        )

        fig.show()

    def calibrate_eyes(self, ear_avg):
        self.ear_values.append(ear_avg)

        if len(self.ear_values) < self.calibration_frames:
            return None

        if not self.eye_calibrated:
            sorted_ear = sorted(self.ear_values)
            upper_40_50 = sorted_ear[int(len(sorted_ear)*0.5):int(len(sorted_ear)*0.6)]
            self.eye_threshold = np.mean(upper_40_50)
            self.eye_calibrated = True
            self.logger.info(' ┌─────────────────────────────────────────────────────────────────────────────┐')
            self.logger.info(' |          Eyes Calibration Complete                                          |')
            self.logger.info(f' |          EAR Threshold: {self.eye_threshold:.3f}                                    |')
            self.logger.info(' └─────────────────────────────────────────────────────────────────────────────┘')

            self.plot_ear_threshold_graph()
        return self.eye_threshold