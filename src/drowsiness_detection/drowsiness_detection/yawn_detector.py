#!/usr/bin/env python3
import numpy as np
from scipy.spatial import distance as dist
import time

"""""
1.  calibration_frames : 시스템 시작 후 일정 시간을 정상 상태로 가정
2.  calibration_mar_values : 정상 상태 기간 동안 검출된 얼굴 지표
3.  calibration_mar_values → 평균 baseline_mean, 표준편차 baseline_std 산출 → 하품 판단 임계치 threshold 도출
    threshold : k_threshold 값을 조정하며 실험으로 도출 
4.  moving_avg_window수 만큼 mar_values 를 mar_moving 변수에 저장 후 평균을 산출하여 이동평균 값 mar_avg_values 도출


"""""
def print_calibration_progress(current, total, bar_length=30):
    """
    콘솔에 ASCII 형태의 진행률 바(Progress Bar)를 표시하는 함수.
    current: 현재 수집된 값(프레임 수 등)
    total: 필요한 총 값
    bar_length: 막대 길이 (문자 수)
    """
    ratio = current / total
    filled_length = int(bar_length * ratio)

    bar_str = "#" * filled_length + "-" * (bar_length - filled_length)
    # \r 로 줄의 맨 앞으로 이동하고, end=""로 줄바꿈 없이 출력
    print(f"\rCalibrating: |{bar_str}| {ratio*100:.1f}% ({current}/{total})", end="")

    # 100% 도달 시 줄바꿈
    if current == total:
        print()

class YawnDetector:
    def __init__(
        self, 
        calibration_frames=300, 
        k_threshold=3, 
        moving_avg_window=20,
        time_threshold=3,
        cooldown_interval=5,
    ):
        self.calibration_frames = calibration_frames 
        self.k_threshold = k_threshold  
        self.moving_avg_window = moving_avg_window
        self.time_threshold = time_threshold
        self.cooldown_interval = cooldown_interval

        self.calibration_mar_values = []
        self.mar_moving = []
        self.calibrated = False

        self.baseline_mean = 0.0
        self.baseline_std = 0.0
        self.threshold = 0.0

        self.candidate_start_time = None
        self.grace_period = 0.5
        self.last_high_mar_time = None
        self.last_yawn_time = None
        self.yawn_count = 0
        self.yawn_sessions = []

        self.status = "Normal"

    def detect(self, landmarks):
        A = dist.euclidean(landmarks[50], landmarks[58]) 
        B = dist.euclidean(landmarks[52], landmarks[56])  
        C = dist.euclidean(landmarks[48], landmarks[54])  
        mar_values = (A + B) / (2.0 * C)

        # 이동 평균 적용
        self.mar_moving.append(mar_values)
        if len(self.mar_moving) > self.moving_avg_window:
            self.mar_moving.pop(0)

        mar_avg_values = np.mean(self.mar_moving)
        current_time = time.time()

        # 하품 여부 판단
        if mar_values > self.threshold:
            self.last_high_mar_time = current_time
            # 입 벌림 시작 시 
            if self.candidate_start_time is None:
                self.candidate_start_time = current_time
            # 입 벌림 시작 후 3초 지속 시 
            elif current_time - self.candidate_start_time >= self.time_threshold:
                self.status = "Yawning"
        else:   
            # 하품 유지 중인데 순간적으로만 MAR이 떨어진 경우
            if self.status == "Yawning" and self.last_high_mar_time and \
                current_time - self.last_high_mar_time <= self.grace_period:
                pass 
            # 진짜로 하품 종료
            elif self.status == "Yawning" and \
                current_time - self.last_high_mar_time >= self.grace_period:
                self.yawn_count += 1
                self.last_yawn_time = current_time
                self.status = "Normal"
                self.candidate_start_time = None
                self.last_high_mar_time = None
            # 하품 안할 때 
            elif self.candidate_start_time:    
                self.candidate_start_time = None

        # 쿨다운으로 세션 기록
        if (
            self.last_yawn_time is not None
            and current_time - self.last_yawn_time > self.cooldown_interval
            and self.yawn_count > 0
        ):
            self.yawn_sessions.append({
                ""
                "end_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time)),
                "yawn_count": self.yawn_count,
            })
            self.yawn_count = 0
            self.last_yawn_time = None

        return mar_avg_values

    def calibrate_mouth(self, mar_avg_values):
        """
        캘리브레이션 로직:
        1) 일정 수(calibration_frames)의 MAR 샘플을 모음
        2) 평균과 표준편차를 구해 Threshold 계산
        3) Threshold가 0.5보다 작으면 재캘리브레이션
        """
        if self.calibrated:
            return self.baseline_mean, self.baseline_std, self.threshold

        if len(self.calibration_mar_values) < self.calibration_frames:
            self.calibration_mar_values.append(mar_avg_values)
            self.status = "Calibrating..."
        else:
            if not self.calibrated:
                self.baseline_mean = np.mean(self.calibration_mar_values)
                self.baseline_std = np.std(self.calibration_mar_values)
                self.threshold = self.baseline_mean + self.k_threshold * self.baseline_std

                if self.threshold < 0.5 :
                    print("Recalibrating... Threshold too low")
                    self.reset_calibration()
                else:
                    self.calibrated = True
                    self.status = "Normal"
                print(
                    f"[Mouth Calibration Complete] Mean: {self.baseline_mean:.3f}, "
                    f"Std: {self.baseline_std:.3f}, Threshold: {self.threshold:.3f}"
                )
        return self.baseline_mean, self.baseline_std, self.threshold
    
    def reset_calibration(self):
        """
        캘리브레이션 상태를 리셋하고 다시 시작
        """
        self.calibrated = False
        self.calibration_mar_values.clear()
        self.baseline_mean = 0.0
        self.baseline_std = 0.0
        self.threshold = 0.0
        self.status = "Recalibrating..."

def start_calibraion_instruction():
    print("캘리브레이션을 시작합니다. 화면에 보이는 단어를 정확한 입모양으로 말해주세요")
    time.sleep(2)

    syllables = ["아", "에", "이", "오", "우"]
    for syl in syllables:
        print(f"단어: {syl}")
        time.sleep(3)

    print("캘리브레이션 종료. 졸음 운전 감지 프로그램을 시작합니다.\n")

if __name__ == "__main__":
    yawn_detector = YawnDetector()

    start_calibraion_instruction()

    import random
    for i in range(80):
        # 가짜 mar_avg_values
        mar_fake = random.uniform(0.2, 0.6)
        yawn_detector.calibrate_mouth(mar_fake)
        time.sleep(0.05)
    
