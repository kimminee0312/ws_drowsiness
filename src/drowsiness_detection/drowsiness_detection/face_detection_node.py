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
        self.subscription_uid = self.create_subscription(
            String,
            '/current_uid',
            self.uid_callback,
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
        
        self.publisher_kal = self.create_publisher(
            Float32MultiArray, 
            '/face/landmarks_kal', 
            10)
        
        self.bridge = CvBridge()
        self.detector = dlib.get_frontal_face_detector()
        model_path = os.path.expanduser("~/workspace/ws_drowsiness/src/drowsiness_detection/drowsiness_detection/shape_predictor_68_face_landmarks.dat")
        self.predictor = dlib.shape_predictor(model_path)

        # 클래스 내 칼만 필터 68개 초기화
        self.kalman_filters = [PointKalman() for _ in range(68)]
        
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

    def uid_callback(self, msg):
        if msg.data.startswith("[drowsy]"):
            self.active = True
            self.get_logger().info(' ┌────────────────────────────────────────────────────────────────────┐')
            self.get_logger().info(' |                         [drowsy] uid 수신                        |')
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
        raw_landmarks = np.array([(shape.part(i).x, shape.part(i).y) for i in range(68)])

        msg_raw = Float32MultiArray()
        msg_raw.data = raw_landmarks.astype(np.float32).flatten().tolist()
        self.publisher.publish(msg_raw)

        smoothed_landmarks = []
        for i, (x,y) in enumerate(raw_landmarks):
            smooth_x, smooth_y = self.kalman_filters[i].correct_and_predict(x,y)
            smoothed_landmarks.append((smooth_x, smooth_y))

        # ROS 메시지 변환
        msg_kal = Float32MultiArray()
        msg_kal.data = np.array(smoothed_landmarks, dtype=np.float32).flatten().tolist()
        self.publisher_kal.publish(msg_kal)

class PointKalman:
    def __init__(self):
        self.frame_count = 0
        self.initialized = False

        # 상태 벡터 4차원, 측정 벡터 2차원
        self.kalman = cv2.KalmanFilter(4, 2)
        self.kalman.measurementMatrix = np.array([[1,0,0,0],
                                                  [0,1,0,0]], np.float32)
        # A 행렬 (상태 전이 모델) : 등속도 모델을 표현
        self.kalman.transitionMatrix = np.array([[1, 0, 1, 0],
                                                  [0, 1, 0, 1],
                                                  [0, 0, 1, 0],
                                                  [0, 0, 0, 1]], np.float32)
        # Q 행렬 (프로세스 잡음 공분산) : Q 행렬 (프로세스 잡음 공분산), 큰 값을 줄수록 "측정을 더 신뢰"
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.001
        # R 행렬 (측정 잡음 공분산) : 측정값(x, y)에 포함된 센서 노이즈를 정의
        self.kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.1
        # P 행렬 (오차 공분산 초기값) : 필터가 얼마나 현재 추정을 믿는지를 수치화
        self.kalman.errorCovPost = np.eye(4, dtype=np.float32)

    def correct_and_predict(self, x, y):
        self.frame_count += 1

        # 초기화 (처음 1회)
        if not self.initialized:
            self.kalman.statePre = np.array([[x], [y], [0], [0]], dtype=np.float32)
            self.kalman.statePost = self.kalman.statePre.copy()
            self.initialized = True

        # 초기 프레임은 필터 없이 raw 값 반환
        if self.frame_count <= 30:
            return x, y
        
        # 측정값이 너무 비정상적이면 무시 (예: (0, 0) 같은 값)
        if x == 0.0 and y == 0.0:
            # 이전 상태 그대로 사용
            prediction = self.kalman.predict()
            return prediction[0, 0], prediction[1, 0]

        measurement = np.array([[np.float32(x)], [np.float32(y)]])
        self.kalman.correct(measurement)
        prediction = self.kalman.predict()

        # 예측값도 안전 범위로 보정
        if abs(prediction[0, 0]) < 1e-3 and abs(prediction[1, 0]) < 1e-3:
            # 거의 0에 수렴한 값이면 이전 상태 유지
            return x, y
        return prediction[0, 0], prediction[1, 0]

def main(args=None):
    rclpy.init(args=args)
    node = FaceDetectorNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
