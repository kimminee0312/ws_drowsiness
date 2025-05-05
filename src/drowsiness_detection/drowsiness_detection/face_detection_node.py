import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String, Bool
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
import cv2
import dlib
import numpy as np
import os

class FaceDetectorNode(Node):
    def __init__(self):
        super().__init__('face_detection_node')

        self.active = False # 이메일 prefix 체크
        self.authenticated = False  # 얼굴 인증 성공 여부

        self.subscription_auth = self.create_subscription(
            Bool,
            '/user_authenticated',
            self.auth_callback,
            10
        )
        self.subscription_email = self.create_subscription(
            String,
            '/current_email',
            self.email_callback,
            10
        )
        self.subscription = self.create_subscription(
            Image, 
            # '/camera/camera/color/image_raw', # Using RGBD Camera
            '/camera/image_raw',
            self.image_callback, 
            10)
        
        self.publisher = self.create_publisher(
            Float32MultiArray, 
            '/face/landmarks', 
            10)
        
        self.bridge = CvBridge()
        self.detector = dlib.get_frontal_face_detector()
        model_path = os.path.expanduser("~/workspace/ws_drowsiness/src/drowsiness_detection/drowsiness_detection/shape_predictor_68_face_landmarks.dat")
        self.predictor = dlib.shape_predictor(model_path)
        
        self.get_logger().info(' ┌────────────────────────────────────────────┐')
        self.get_logger().info(' |           Face Detector Node Start         |')
        self.get_logger().info(' └────────────────────────────────────────────┘')
        
    def auth_callback(self, msg):
        self.authenticated = msg.data
        if self.authenticated:
            self.get_logger().info(' ┌────────────────────────────────────────────────────────────────────┐')
            self.get_logger().info(' |                               얼굴 인증 성공                       |')
            self.get_logger().info(' └────────────────────────────────────────────────────────────────────┘')
        else:
            self.get_logger().info(' ┌────────────────────────────────────────────────────────────────────┐')
            self.get_logger().info(' |                               얼굴 인증 실패                          |')
            self.get_logger().info(' └────────────────────────────────────────────────────────────────────┘')

    def email_callback(self, msg):
        if msg.data.startswith("[drowsy]"):
            self.active = True
            self.get_logger().info(' ┌────────────────────────────────────────────────────────────────────┐')
            self.get_logger().info(' |                         [drowsy] email 수신                        |')
            self.get_logger().info(' └────────────────────────────────────────────────────────────────────┘')

        else:
            self.active = False
            self.get_logger().info(' ┌────────────────────────────────────────────────────────────────────┐')
            self.get_logger().info(' |                     [drowsy] prefix 없음 →  비활성화                  |')
            self.get_logger().info(' └────────────────────────────────────────────────────────────────────┘')

    def image_callback(self, msg):
        # [drowsy] prefix 안 오면 동작 안 함
        if not (self.active and self.authenticated):
            return  
        
        frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)

        if len(faces) == 0:
            return
        
        shape = self.predictor(gray, faces[0])
        landmarks = np.array([(shape.part(i).x, shape.part(i).y) for i in range(68)])

        # ROS 메시지 변환
        msg = Float32MultiArray()
        msg.data = landmarks.astype(np.float32).flatten().tolist()
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = FaceDetectorNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
