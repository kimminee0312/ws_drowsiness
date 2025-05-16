import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
import numpy as np
from .eye_detection_node import EyeDetector
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
        
        self.subscription = self.create_subscription(
            String, 
            '/eyes/status',
            self.eyes_status_callback, 
            10)
        
        self.publisher = self.create_publisher(
            String, 
            '/drowsiness/status', 
            10)
        
        self.nodding_detector = NoddingDetector()
        
        self.yawn_status = None
        self.eyes_status = None

        self.get_logger().info(' ┌────────────────────────────────────────────┐')
        self.get_logger().info(' |       Drowsiness Detection Node Start      |')
        self.get_logger().info(' └────────────────────────────────────────────┘')

    # -----------------------------
    # 1) 하품 상태 감지 콜백
    # -----------------------------
    def yawn_status_callback(self, msg):
        self.yawn_status = msg.data 

    # -----------------------------
    # 2) 눈 감김 상태 감지 콜백
    # -----------------------------
    def eyes_status_callback(self, msg):
        self.eyes_status = msg.data         

    # -----------------------------
    # 3) 졸음 분석 및 점수 부여 알고리즘 
    # -----------------------------
    def analyze_drowsiness(self, nodding_status, yawn_status, eyes_status):
        status_parts = []

        if (yawn_status in ["Mouth Calibrating...", "Recalibrating..."] or
            eyes_status == "Eyes Calibrating..."):
            return "Calibrating Now"

        if eyes_status == "CLOSED":
            status_parts.append("눈 감김")

        if nodding_status == "Nodding" and eyes_status == "CLOSED":
            status_parts.append("앞으로 끄덕임")

        if nodding_status == "Nodding_Side" and eyes_status == "CLOSED":
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
    # 4) 메인 콜백
    # -----------------------------
    def drowsiness_detection_callback(self, msg):
        landmarks = np.array(msg.data).reshape(-1, 2)

        nodding_status = self.nodding_detector.detect(landmarks)
        yawn_status = self.yawn_status
        eyes_status = self.eyes_status

        status = self.analyze_drowsiness(nodding_status, yawn_status, eyes_status)
        self.publisher.publish(String(data=status))

def main(args=None):
    rclpy.init(args=args)
    node = DrowsinessDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
