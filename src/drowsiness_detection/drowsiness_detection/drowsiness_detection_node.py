import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String, Float32
import numpy as np

from .eye_detector import EyeDetector
from .nodding_detector import NoddingDetector

class DrowsinessDetectionNode(Node):
    def __init__(self):
        super().__init__('drowsiness_detection_node')

        self.subscription = self.create_subscription(
            Float32MultiArray, 
            '/face/landmarks', 
            self.drowsiness_detection_callback, 
            10)
        self.subscription = self.create_subscription(
            String, 
            '/yawn/status',
            self.yawn_status_callback, 
            10)
        
        self.publisher = self.create_publisher(
            String, 
            '/drowsiness/status', 
            10)
        
        self.publisher_ear = self.create_publisher(
            Float32, 
            '/debug/ear/status', 
            10)
        
        self.eye_detector = EyeDetector(self.get_logger())
        self.nodding_detector = NoddingDetector()

        self.eye_closed_start_time = None
        self.eye_closed_duration_threshold = 2.0 
        
        self.yawn_status = None

        # 상태 관리
        self.mouth_calibrated = False
        self.eye_calibration_started = False
        self.calibration_sleep_done = False
        self.sleep_after_mouth = 3.0  # 3초 대기

        # 타이머 초기화
        self.mouth_done_time = None

        # 눈 슬라이딩 윈도우 적용 파라미터 
        self.ear_history = []
        self.ear_window_size = 20

        self.get_logger().info(' ┌────────────────────────────────────────────┐')
        self.get_logger().info(' |       Drowsiness Detection Node Start      |')
        self.get_logger().info(' └────────────────────────────────────────────┘')

    # -----------------------------
    # 1) 캘리브레이션 함수 
    # -----------------------------
    def is_calibrating(self, ear_avg):
        if self.yawn_status == "Recalibrating...":
            self.publisher.publish(String(data="Mouth Calibrating..."))
            return True

        # 입 캘리브레이션 중
        if self.yawn_status =="Mouth Calibrating..." and not self.mouth_calibrated:
            self.publisher.publish(String(data="Mouth Recalibrating..."))
            return True

        # 입 캘리브레이션 완료 후 상태 변경
        if self.yawn_status == "Mouth Calibration Complete" and not self.mouth_calibrated:
            self.mouth_calibrated = True
            self.mouth_done_time = time.time()
            self.get_logger().info(' ┌────────────────────────────────────────────┐')
            self.get_logger().info(' |        Mouth Calibration Complete          |')
            self.get_logger().info(' └────────────────────────────────────────────┘')
            self.publisher.publish(String(data="Mouth Calibration Complete"))
            return True

        # 입 캘리브레이션 완료 후 슬립 시간 중
        if self.mouth_calibrated and not self.calibration_sleep_done:
            if time.time() - self.mouth_done_time < self.sleep_after_mouth:
                return True
            else:
                # 슬립 시간 완료
                self.calibration_sleep_done = True
                self.get_logger().info(' ┌────────────────────────────────────────────┐')
                self.get_logger().info(' |            Eyes Calibration start          |')
                self.get_logger().info(' └────────────────────────────────────────────┘')
        
        # 눈 캘리브레이션 수행은 반드시 위 조건이 끝난 뒤에 시작
        if self.mouth_calibrated and self.calibration_sleep_done:
            eye_threshold = self.eye_detector.calibrate_eyes(ear_avg)

            # 슬립 타입 완료 후 입 캘리브레이션 시작
            if  eye_threshold is None:
                self.publisher.publish(String(data="Eyes Calibrating..."))
                return True

            # 입 캘리브레이션 완료 후 상태 변경 
            if not self.eye_calibration_started:
                self.eye_calibration_started = True
                self.get_logger().info(' ┌────────────────────────────────────────────┐')
                self.get_logger().info(' |         Eyes Calibration Complete          |')
                self.get_logger().info(' └────────────────────────────────────────────┘')
                self.publisher.publish(String(data="Eyes Calibration Complete"))
                return False
        return False
        
    # -----------------------------
    # 2) 눈 감김 시간 로직 함수
    # -----------------------------
    def check_eyes_closed(self, ear_avg):
        """
        슬라이딩 윈도우 평균 적용 후 EAR < eye_threshold 상태가 2초 이상 유지되면 True 반환
        그렇지 않으면 False`
        """

        self.ear_history.append(ear_avg)
        if len(self.ear_history) > self.ear_window_size:
            self.ear_history.pop(0)

        smoothed_ear = np.mean(self.ear_history)

        if smoothed_ear < self.eye_detector.eye_threshold:
            if self.eye_closed_start_time is None :
                self.eye_closed_start_time = time.time()
            else:
                duration = time.time() - self.eye_closed_start_time
                if duration >= self.eye_closed_duration_threshold:
                    return True
        else:
            self.eye_closed_start_time = None
        return False
    
    # -----------------------------
    # 3) 하품 상태 감지 콜백
    # -----------------------------
    def yawn_status_callback(self, msg):
        self.yawn_status = msg.data 

    # -----------------------------
    # 4) 졸음 분석 및 점수 부여 알고리즘 
    # -----------------------------
    def analyze_drowsiness(self, eyes_closed_status, nodding_status, yawn_status):
        status_parts = []

        if eyes_closed_status:
            status_parts.append("눈 감김")

        if nodding_status == "Nodding" and eyes_closed_status:
            status_parts.append("앞으로 끄덕임")

        if nodding_status == "Nodding_Side" and eyes_closed_status:
            status_parts.append("옆으로 끄덕임")

        if yawn_status == "Yawn candidate":
            status_parts.append("하품 후보")
        elif yawn_status == "Yawning":
            status_parts.append("하품 감지")

        if not status_parts:
            return "Normal"

        else:
            return " / ".join(status_parts)

    # -----------------------------
    # 5) 메인 콜백
    # -----------------------------
    def drowsiness_detection_callback(self, msg):
        landmarks = np.array(msg.data).reshape(-1, 2)

        ear_avg = self.eye_detector.detect(landmarks)
        # For rqt_graph visualization
        self.publisher_ear.publish(Float32(data=ear_avg))

        if self.is_calibrating(ear_avg):
            return
        
        eyes_closed_status = self.check_eyes_closed(ear_avg)
        nodding_status = self.nodding_detector.detect(landmarks)
        yawn_status = self.yawn_status

        # self.get_logger().info(f"[EAR avg]: {ear_avg:.3f}, Threshold: {self.eye_detector.eye_threshold:.3f}")
        # self.get_logger().info(f"[눈 감김 판단]: {eyes_closed_status}")
        # self.get_logger().info(f"[끄덕임 판단]: {nodding_status}")
        # self.get_logger().info(f"[하품 상태]: {yawn_status}")

        status = self.analyze_drowsiness(eyes_closed_status, nodding_status, yawn_status)
        self.publisher.publish(String(data=status))

def main(args=None):
    rclpy.init(args=args)
    node = DrowsinessDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
