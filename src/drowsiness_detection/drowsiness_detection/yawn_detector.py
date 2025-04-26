#!/usr/bin/env python3
import numpy as np
from scipy.spatial import distance as dist
import time

"""""
1.  calibration_frames : 시스템 시작 후 calibration_frames 시간을 정상 상태로 가정
2.  calibration_mar_values : calibration_frames 기간 동안 검출된 mar_avg_values
3.  calibration_mar_values → 평균 baseline_mean, 표준편차 baseline_std 산출 → 하품 판단 임계치 threshold 도출
    threshold : k_threshold 값을 조정하며 실험으로 도출 
    threshold : 동적 캘리브레이션 후 임계치 값이 0.5이하 시 재 캘리브레이션 실행 
4.  moving_avg_window 수 만큼 mar_values 를 mar_moving 변수에 저장 후 평균을 산출하여 이동평균 값 mar_avg_values 도출
5.  mar_avg_values > threshold 이고 candidate_start_time = None 


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
        keep_time_threshold=1,
        cooldown_interval=5,
    ):
        self.calibration_frames = calibration_frames 
        self.k_threshold = k_threshold  
        self.moving_avg_window = moving_avg_window
        self.time_threshold = time_threshold
        self.keep_time_threshold = keep_time_threshold
        self.cooldown_interval = cooldown_interval

        self.calibration_mar_values = []
        self.mar_moving = []
        self.calibrated = False

        self.baseline_mean = 0.0
        self.baseline_std = 0.0
        self.threshold = 0.0

        self.candidate_start_time = None
        self.last_mar_time = None
        self.last_yawn_time = None
        self.yawn_count = 0
        self.yawn_sessions = []

        self.status = "Calibrating..."

    def calibrate_mouth(self, mar_avg_values):
        if self.calibrated:
            return self.baseline_mean, self.baseline_std, self.threshold

        if len(self.calibration_mar_values) < self.calibration_frames:
            self.calibration_mar_values.append(mar_avg_values)
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

        # mar 동적 캘리브레이션 → threshold 산출
        self.calibrate_mouth(mar_avg_values)

        # 하품 여부 판단
        if self.status == "Normal":
            if mar_avg_values >= self.threshold:
                self.status = "Yawn candidate" 
                self.candidate_start_time = current_time
            else:
                pass

        elif self.status == "Yawn candidate":
            if mar_avg_values >= self.threshold:
                if current_time - self.candidate_start_time >= self.time_threshold:
                    self.status = "Yawning"
                else:
                    pass
            elif mar_avg_values < self.threshold:
                if self.last_mar_time is None:
                    self.last_mar_time = current_time
                elif current_time - self.last_mar_time <= self.keep_time_threshold:
                    pass
                elif current_time - self.last_mar_time > self.keep_time_threshold:
                    self.status = "Normal"
                    self.candidate_start_time = None
                    self.last_mar_time = None

        elif self.status == "Yawning":
            if mar_avg_values >= self.threshold:
                pass
            elif mar_avg_values < self.threshold:
                if self.last_mar_time is None :
                    self.last_mar_time = current_time
                elif self.last_mar_time is not None and current_time - self.last_mar_time > self.keep_time_threshold:
                    self.yawn_count +=1
                    self.last_yawn_time = current_time
                    self.status = "Normal"
                    self.candidate_start_time = None
                    self.last_mar_time = None
            

        # 쿨다운으로 세션 기록
        if (
            self.last_yawn_time is not None
            and current_time - self.last_yawn_time > self.cooldown_interval
            and self.yawn_count > 0
        ):
            self.yawn_sessions.append({
                "end_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time)),
                "yawn_count": self.yawn_count,
            })
            self.yawn_count = 0
            self.last_yawn_time = None

        return mar_avg_values

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

