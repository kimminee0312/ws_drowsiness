#!/usr/bin/env python3
import numpy as np
from scipy.spatial import distance as dist
import time


class YawnDetector:
    def __init__(
        self, 
        calibration_frames=70, 
        k_threshold=4, 
        moving_avg_window=20,
    ):
        self.calibration_frames = calibration_frames 
        self.k_threshold = k_threshold  
        self.moving_avg_window = moving_avg_window

        self.mar_values = []
        self.calibrated = False
        self.baseline_mean = 0.0
        self.baseline_std = 0.0
        self.threshold = 0.0

        self.mar_moving = []
        self.status = "Normal"

    def detect(self, landmarks):
        A = dist.euclidean(landmarks[50], landmarks[58]) 
        B = dist.euclidean(landmarks[52], landmarks[56])  
        C = dist.euclidean(landmarks[48], landmarks[54])  
        mar = (A + B) / (2.0 * C)

        self.mar_moving.append(mar)
        if len(self.mar_moving) > self.moving_avg_window:
            self.mar_moving.pop(0)

        mar_avg = np.mean(self.mar_moving)
        return mar_avg

    def calibrate_mouth(self, mar_avg):
        """
        캘리브레이션 로직:
        1) 일정 수(calibration_frames)의 MAR 샘플을 모음
        2) 평균과 표준편차를 구해 Threshold 계산
        3) Threshold가 0.5보다 작으면 재캘리브레이션
        """
        if self.calibrated:
            return self.baseline_mean, self.baseline_std, self.threshold

        if len(self.mar_values) < self.calibration_frames:
            self.mar_values.append(mar_avg)
            self.status = "Calibrating..."
        else:
            if not self.calibrated:
                self.baseline_mean = np.mean(self.mar_values)
                self.baseline_std = np.std(self.mar_values)
                self.threshold = self.baseline_mean + self.k_threshold * self.baseline_std
                self.calibrated = True

                print(f"outh Calibration done:  Baseline Mean = {self.baseline_mean:.3f}, Baseline Std = {self.baseline_std:.3f}, Threshold = {self.threshold:.3f}")

                if self.threshold < 0.5 :
                    print(
                        "The calibratin value is invalid"
                        "\n"
                        "\n"
                        "\n"
                        "Recalibrating..."
                    )
                    self.reset_calibration()
                else:
                    self.calibrated = True
                    self.status = "Normal"
        return self.baseline_mean, self.baseline_std, self.threshold
    
    def reset_calibration(self):
        """
        캘리브레이션 상태를 리셋하고 다시 시작
        """
        self.calibrated = False
        self.mar_values = []
        self.baseline_mean = 0.0
        self.baseline_std = 0.0
        self.threshold = 0.0
        self.status = "Calibrating..."

def start_calibraion_instruction():
    print("캘리브레이션을 시작합니다. 화면에 보이는 단어를 정확한 입모양으로 말해주세요")
    time.sleep(2)

    syllables = ["아", "에", "이", "오", "우"]
    for syl in syllables:
        print(f"단어: {syl}")
        time.sleep(3)

if __name__ == "__main__":
    yawn_detector = YawnDetector

    start_calibraion_instruction()

    
