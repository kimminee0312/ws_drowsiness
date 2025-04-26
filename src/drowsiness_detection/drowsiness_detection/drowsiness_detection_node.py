import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
import numpy as np

from .eye_detector import EyeDetector
from .yawn_detector import YawnDetector
from .nodding_detector import NoddingDetector

class DrowsinessDetectionNode(Node):
    def __init__(self):
        super().__init__('drowsiness_detection_node')
        self.subscription = self.create_subscription(
            Float32MultiArray, 
            '/face/landmarks', 
            self.drowsiness_detection_callback, 
            10)
        self.publisher = self.create_publisher(
            String, 
            '/drowsiness/status', 
            10)
        
        self.eye_detector = EyeDetector()
        self.yawn_detector = YawnDetector()
        self.nodding_detector = NoddingDetector()

        self.eye_closed_start_time = None
        self.eye_closed_duration_threshold = 2.0 
        
        self.get_logger().info(' ┌────────────────────────────────────────────┐')
        self.get_logger().info(' |       Drowsiness Detection Node Start      |')
        self.get_logger().info(' └────────────────────────────────────────────┘')

    # -----------------------------
    # 1) 눈 감김 시간 로직 함수
    # -----------------------------
    def check_eyes_closed(self, ear_avg):
        """
        EAR < eye_threshold 상태가 2초 이상 유지되면 True 반환
        그렇지 않으면 False
        """
        if ear_avg < self.eye_detector.eye_threshold:
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
    # 3) 메인 콜백: 졸음 인식
    # -----------------------------
    def drowsiness_detection_callback(self, msg):
        landmarks = np.array(msg.data).reshape(-1, 2)

        ear_avg = self.eye_detector.detect(landmarks)
        self.eye_detector.calibrate_eyes(ear_avg)

        nodding_status = self.nodding_detector.detect(landmarks)

        if (not self.yawn_detector.calibrated) or (not self.eye_detector.eye_calibrated):
            status = "Calibrating ..."
            self.publisher.publish(String(data=status))
            return 
        
        eyes_closed_status = self.check_eyes_closed_status(ear_avg)
        yawn_status = self.yawn_detector.status
        
        status_parts = []

        if eyes_closed_status:
            status_parts.append("눈 감김")

        if nodding_status == "Nodding":
            status_parts.append("앞으로 끄덕임")

        if nodding_status == "Nodding_side":
            status_parts.append("옆으로 끄덕임")

        if yawn_status == "Yawn candidate":
            status_parts.append("하품 후보")
        elif yawn_status == "Yawning":
            status_parts.append("하품 감지")

        if not status_parts:
            status = "Normal"

        else:
            status = " / ".join(status_parts)

        self.publisher.publish(String(data=status))

def main(args=None):
    rclpy.init(args=args)
    node = DrowsinessDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
