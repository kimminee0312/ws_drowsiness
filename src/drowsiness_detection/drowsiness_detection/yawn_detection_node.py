#!/usr/bin/env python3
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
import numpy as np
from scipy.spatial import distance as dist

"""""
1.  calibration_frames : 시스템 시작 후 calibration_frames 시간을 정상 상태로 가정
2.  calibration_mar_values : calibration_frames 기간 동안 검출된 mar_avg_values
3.  calibration_mar_values → 평균 baseline_mean, 표준편차 baseline_std 산출 → 하품 판단 임계치 threshold 도출
    threshold : k_threshold 값을 조정하며 실험으로 도출 
    threshold : 동적 캘리브레이션 후 임계치 값이 0.5이하 시 재 캘리브레이션 실행 
4.  moving_avg_window 수 만큼 mar_values 를 mar_moving 변수에 저장 후 평균을 산출하여 이동평균 값 mar_avg_values 도출
5.  mar_avg_values > threshold 이고 candidate_start_time = None 


"""""
class YawnDetectionNode(Node):
    def __init__(self):
        super().__init__('yawn_detection_node')
        self.subscription = self.create_subscription(
            Float32MultiArray, 
            '/face/landmarks', 
            self.yawn_detection_callback, 
            10)
        self.subscription = self.create_subscription(
            String, 
            '/drowsiness/status', 
            self.drowsiness_status_callback,
            10)

        self.publisher = self.create_publisher(
            String, 
            '/yawn/status', 
            10)
        
        self.yawn_detector = YawnDetector(self.get_logger())

        self.get_logger().info(' ┌───────────────────────────────────────────────┐')
        self.get_logger().info(' |            Yawn Detection Node Start          |')
        self.get_logger().info(' └───────────────────────────────────────────────┘')

    # -----------------------------
    #  하품 상태 감지 콜백
    # -----------------------------
    def drowsiness_status_callback(self, msg):
        self.drowsiness_status = msg.data 
        self.yawn_detector.drowsiness_status = msg.data 

    def yawn_detection_callback(self, msg):
        landmarks = np.array(msg.data).reshape(-1, 2)

        # 이동 평균 적용
        mar_avg_values = self.yawn_detector.detect(landmarks)
        # 캘리브레이션
        self.yawn_detector.calibrate_mouth(mar_avg_values)

        # 캘리브레이션 완료 시 하품 감지
        if self.yawn_detector.calibrated:
            self.yawn_detector.yawn_detect(mar_avg_values)

        # 현재 하품 상태 퍼블리시
        status = self.yawn_detector.status
        self.publisher.publish(String(data=status))
class YawnDetector:
    def __init__(
        self, 
        logger,
        calibration_frames=300, 
        k_threshold=3, 
        moving_avg_window=20,
        time_threshold=3,
        keep_time_threshold=1,
        cooldown_interval=180, 
    ):
        self.logger = logger
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

        self.status = "Mouth Calibrating..."
        self.drowsiness_status = None

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
        return mar_avg_values

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
                    self.logger.info(' ┌─────────────────────────────────────────────────────────────────────────────┐')
                    self.logger.info(' |          Recalibrating... Threshold too low                                 |')
                    self.logger.info(' └─────────────────────────────────────────────────────────────────────────────┘')
                                     
                    self.reset_calibration()
                elif self.threshold > 0.9 :
                    self.logger.info(' ┌─────────────────────────────────────────────────────────────────────────────┐')
                    self.logger.info(' |          Recalibrating... Threshold too high                                |')
                    self.logger.info(' └─────────────────────────────────────────────────────────────────────────────┘')
                    self.reset_calibration()
                else:
                    self.calibrated = True
                    self.status = "Mouth Calibration Complete"
                    self.logger.info(' ┌─────────────────────────────────────────────────────────────────────────────┐')
                    self.logger.info(' |          Mouth Calibration Complete                                         |')
                    self.logger.info(f' |          Mean: {self.baseline_mean:.3f}, Std: {self.baseline_std:.3f}, Threshold: {self.threshold:.3f}                          |')
                    self.logger.info(' └─────────────────────────────────────────────────────────────────────────────┘')
        
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

    def yawn_detect(self, mar_avg_values):
        current_time = time.time()

        if not self.calibrated:
            return
        
        # 하품 여부 판단
        if self.status == "Mouth Calibration Complete" and self.drowsiness_status =="Normal":
            self.status = "Normal"

        elif self.status == "Normal":
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
        if (self.last_yawn_time is not None and 
            current_time - self.last_yawn_time > self.cooldown_interval and 
            self.yawn_count > 0):
            self.yawn_sessions.append({
                "end_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time)),
                "yawn_count": self.yawn_count,
            })
            self.logger.info(' ┌─────────────────────────────────────────────────────────────────────────────────────┐')
            self.logger.info(f' |          Yawn Session Record  {self.yawn_sessions[-1]}')
            self.logger.info(' └─────────────────────────────────────────────────────────────────────────────────────┘')

            self.yawn_count = 0
            self.last_yawn_time = None

        return mar_avg_values
    
def main(args=None):
    rclpy.init(args=args)
    node = YawnDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()

