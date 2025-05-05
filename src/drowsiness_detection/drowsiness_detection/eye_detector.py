#!/usr/bin/env python3
import numpy as np
from scipy.spatial import distance as dist
import plotly.graph_objects as go


class EyeDetector:
    def __init__(self, logger, calibration_frames=200, k_eye=0.7):
        self.logger = logger
        self.calibration_frames = calibration_frames
        self.k_eye = k_eye
        self.ear_values = []
        self.eye_calibrated = False
        self.baseline_ear = 0
        self.eye_threshold = 0

    def plot_ear_calibration(self, ear_values, baseline_ear, threshold):
        x_vals = list(range(len(ear_values)))

        fig = go.Figure()

        # EAR 값들 (초록)
        fig.add_trace(go.Scatter(
            x=x_vals, y=ear_values, mode='markers', name='EAR 값',
            marker=dict(color='lime', size=6)
        ))

        # Baseline EAR (파랑)
        fig.add_trace(go.Scatter(
            x=x_vals, y=[baseline_ear]*len(ear_values),
            mode='lines+markers', name='Baseline EAR',
            marker=dict(color='blue', size=5), line=dict(dash='dash')
        ))

        # Threshold (빨강)
        fig.add_trace(go.Scatter(
            x=x_vals, y=[threshold]*len(ear_values),
            mode='lines+markers', name='Threshold',
            marker=dict(color='red', size=5), line=dict(dash='dot')
        ))

        fig.update_layout(
            title='EAR Calibration Visualization',
            xaxis_title='Frame Index',
            yaxis_title='EAR Value',
            template='plotly_white',
            height=500
        )

        fig.show()

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

    def calibrate_eyes(self, ear_avg):
        if len(self.ear_values) < self.calibration_frames:
            self.ear_values.append(ear_avg)
        else:
            if not self.eye_calibrated:
                self.baseline_ear = np.mean(self.ear_values)
                std_ear = np.std(self.ear_values)
            
                self.eye_threshold = self.baseline_ear - self.k_eye * std_ear
                self.eye_calibrated = True
                self.logger.info(' ┌─────────────────────────────────────────────────────────────────────────────┐')
                self.logger.info(' |          Eyes Calibration Complete                                          |')
                self.logger.info(f' |          Baseline EAR: {self.baseline_ear:.3f},EAR Threshold: {self.eye_threshold:.3f}                           |')
                self.logger.info(' └─────────────────────────────────────────────────────────────────────────────┘')

                # 시각화
                self.plot_ear_calibration(
                    self.ear_values,
                    self.baseline_ear,
                    self.eye_threshold
                )

        return self.baseline_ear, self.eye_threshold