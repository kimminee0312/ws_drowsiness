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

        self.eye_threshold = None
        self.closed_mean = None
        self.opened_mean = None


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

        # Lower Threshold (파란 점선)
        if self.closed_mean is not None:
            fig.add_trace(go.Scatter(
                x=x_vals, y=[self.closed_mean] * len(self.ear_values),
                mode='lines', name='감은 상태 평균 (Lower)',
                line=dict(color='blue', dash='dash')
            ))

        # Upper Threshold (빨간 점선)
        if self.opened_mean is not None:    
            fig.add_trace(go.Scatter(
                x=x_vals, y=[self.opened_mean] * len(self.ear_values),
                mode='lines', name='뜬 상태 평균 (Upper)',
                line=dict(color='red', dash='dash')
            ))

        # Final Threshold (검은 점선)
        if self.eye_threshold is not None:
            fig.add_trace(go.Scatter(
                x=x_vals, y=[self.eye_threshold] * len(self.ear_values),
                mode='lines', name='최종 임계값 (중간값)',
                line=dict(color='black', dash='dot')
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
            unique_ear = sorted(list(set(self.ear_values)))

            if len(unique_ear) >=10:
                closed_ear = unique_ear[:int(len(unique_ear)*0.2)]
                opened_ear = unique_ear[int(len(unique_ear)*0.6):]

            else:
                # 유니크 값 너무 작을 시 정규 분포 가정 성립 X : 기존 방식으로 중복 포함 계산 
                closed_ear = sorted_ear[:int(len(sorted_ear)*0.2)]
                opened_ear = sorted_ear[int(len(sorted_ear)*0.6):]

            closed_mean = np.mean(closed_ear)
            opened_mean = np.mean(opened_ear)
            
            self.closed_mean = closed_mean
            self.opened_mean = opened_mean
            self.eye_threshold = (closed_mean + opened_mean) / 2
            self.eye_calibrated = True

            self.logger.info(' ┌─────────────────────────────────────────────────────────────────────────────┐')
            self.logger.info(' |          Eyes Calibration Complete                                          |')
            self.logger.info(f' |          EAR Threshold: {self.eye_threshold:.3f}                                    |')
            self.logger.info(' └─────────────────────────────────────────────────────────────────────────────┘')

            # 시각화
            self.plot_ear_threshold_graph()
        return self.eye_threshold