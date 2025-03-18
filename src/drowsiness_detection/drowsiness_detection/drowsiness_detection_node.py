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
        self.subscription = self.create_subscription(Float32MultiArray, '/face/landmarks', self.landmarks_callback, 10)
        self.publisher = self.create_publisher(String, '/drowsiness/status', 10)
        self.eye_detector = EyeDetector()
        self.yawn_detector = YawnDetector()
        self.nodding_detector = NoddingDetector()
        self.get_logger().info("😴 Drowsiness Detection Node Started ✅")

    def landmarks_callback(self, msg):
        landmarks = np.array(msg.data).reshape(-1, 2)
        ear_avg = self.eye_detector.detect(landmarks)
        mar_avg = self.yawn_detector.detect(landmarks)
        nodding_status = self.nodding_detector.detect(landmarks)

        if mar_avg > self.yawn_detector.threshold and nodding_status == "Nodding":
            status = "Drowsy (Yawning & Nodding)"
        elif ear_avg < self.eye_detector.eye_threshold:
            status = "Drowsy (Eyes Closed)"
        elif mar_avg > self.yawn_detector.threshold:
            status = "Yawning"
        elif nodding_status == "Nodding":
            status = "Nodding"
        else:
            status = "Normal"

        self.publisher.publish(String(data=status))

def main(args=None):
    rclpy.init(args=args)
    node = DrowsinessDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
