#!/usr/bin/env python3
import numpy as np
from scipy.spatial import distance as dist
import plotly.graph_objects as go
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String, Float32
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point

class EyeDetectionNode(Node):
    def __init__(self):
        super().__init__('eye_detection_node')
        self.subscription = self.create_subscription(
            Float32MultiArray, 
            '/face/landmarks', 
            self.raw_eye_detection_callback, 
            10)
        
        self.subscription_kal = self.create_subscription(
            Float32MultiArray, 
            '/face/landmarks_kal', 
            self.kal_eye_detection_callback, 
            10)

        self.pub_eyes_status = self.create_publisher(
            String, 
            '/eyes/status', 
            10)
        
        self.pub_debug_eye_marker = self.create_publisher(
            Marker, 
            '/debug/eye_landmarks', 
            10)
        
        self.pub_debug_ear_raw = self.create_publisher(
            Float32, 
            '/debug/ear/raw', 
            10)
        
        self.pub_debug_ear_kal = self.create_publisher(
            Float32, 
            '/debug/ear/kal', 
            10)

        self.eye_detector = EyeDetector(self.get_logger())

        self.landmarks_raw = None
        self.landmarks_kalman = None

        self.get_logger().info(' ┌───────────────────────────────────────────────┐')
        self.get_logger().info(' |            Eye Detection Node Start           |')
        self.get_logger().info(' └───────────────────────────────────────────────┘')

    def raw_eye_detection_callback(self, msg):
        self.landmarks_raw = np.array(msg.data).reshape(-1, 2)
        self.try_process()

    def kal_eye_detection_callback(self, msg):
        self.landmarks_kalman = np.array(msg.data).reshape(-1, 2)
        self.try_process()

    def try_process(self):
        if self.landmarks_raw is None or self.landmarks_kalman is None:
            return
    
        self.eye_detector.publish_eye_markers(
            self.landmarks_raw, self.pub_debug_eye_marker, self.get_clock()
        )        

        ear_raw = self.eye_detector.detect(self.landmarks_raw)
        ear_kal = self.eye_detector.detect(self.landmarks_kalman)

        # 디버깅용 퍼블리시
        self.pub_debug_ear_raw.publish(Float32(data=ear_raw)) 
        self.pub_debug_ear_kal.publish(Float32(data=ear_kal)) 

        # 캘리브레이션은 raw로 진행
        self.eye_detector.calibrate_eyes(ear_raw) 

        # 캘리브레이션 완료 시 하품 감지
        if not self.eye_detector.eye_calibrated:
            status = "Eyes Calibrating..."
        else:
            self.eye_detector.update_eye_state(ear_kal) # 상태는 보정된 기준으로
            status = self.eye_detector.eye_state

        self.pub_eyes_status.publish(String(data=status))

        # reset
        self.landmarks_raw = None
        self.landmarks_kalman = None

class EyeDetector:
    def __init__(self, logger, calibration_frames=150, margin_ratio=0.1):
        self.logger = logger
        self.calibration_frames = calibration_frames
        self.ear_values = []
        self.eye_calibrated = False

        self.eye_threshold = None
        self.closed_mean = None
        self.opened_mean = None

        self.margin_ratio = margin_ratio
        self.lower_threshold = None
        self.upper_threshold = None
        self.eye_state = "none" # initial state

        self.closed_start_time = None
        self.open_start_time = None
        self.setting_time = None
        self.closed_duration_threshold = 1.0
        self.open_duration_threshold = 0.3
        self.setting_time_threshold = 0.2

    def publish_eye_markers(self, landmarks, publisher, clock):
        marker = Marker()
        marker.header.frame_id = "map"  # TF 프레임 (카메라 기준이면 camera_link도 가능)
        marker.header.stamp = clock.now().to_msg()
        marker.ns = "eye_landmarks"
        marker.id = 0
        marker.type = Marker.SPHERE_LIST
        marker.action = Marker.ADD
        marker.scale.x = 0.04
        marker.scale.y = 0.04
        marker.scale.z = 0.04
        marker.color.r = 0.5
        marker.color.g = 0.7
        marker.color.b = 0.3
        marker.color.a = 1.0

        for i in list(range(36, 48)):  # 왼쪽, 오른쪽 눈 총 12점
            pt = Point()
            pt.x = float(landmarks[i][0]) / 100.0  # 픽셀 → 미터 단위 스케일 조정
            pt.y = float(landmarks[i][1]) / 100.0
            pt.z = 0.0
            marker.points.append(pt)

        publisher.publish(marker)

    # -----------------------------
    #  눈 특징점 감지 함수
    # -----------------------------
    def detect(self, landmarks):
        def compute_EAR(eye):
            A = dist.euclidean(eye[1], eye[5])
            B = dist.euclidean(eye[2], eye[4])
            C = dist.euclidean(eye[0], eye[3])
            ear = (A + B) / (2.0 * C)
            return ear

        left_eye = landmarks[36:42]
        right_eye = landmarks[42:48]
        left_EAR = compute_EAR(left_eye)
        right_EAR = compute_EAR(right_eye)
        ear_avg = (left_EAR + right_EAR) / 2.0
        return ear_avg

    def calibrate_eyes(self, ear_avg):
        self.ear_values.append(ear_avg)

        if len(self.ear_values) < self.calibration_frames:
            return None

        if not self.eye_calibrated:
            sorted_ear = sorted(self.ear_values)
            unique_ear = sorted(list(set(self.ear_values)))

            if len(unique_ear) >=10:
                closed_ear = unique_ear[:int(len(unique_ear)*0.2)]
                opened_ear = unique_ear[int(len(unique_ear)*0.6):]

            else:
                # 유니크 값 너무 작을 시 정규 분포 가정 성립 X : 기존 방식으로 중복 포함 계산 
                closed_ear = sorted_ear[:int(len(sorted_ear)*0.2)]
                opened_ear = sorted_ear[int(len(sorted_ear)*0.6):]
            
            self.closed_mean = np.mean(closed_ear)
            self.opened_mean = np.mean(opened_ear)
            self.eye_threshold = (self.closed_mean + self.opened_mean) / 2

            self.lower_threshold = self.closed_mean * (1 + self.margin_ratio)
            self.upper_threshold = self.opened_mean * (1 - self.margin_ratio*1.5)
            # self.upper_threshold = self.opened_mean - 0.1

            self.eye_calibrated = True

            self.logger.info(' ┌─────────────────────────────────────────────────────────────────────────────┐')
            self.logger.info(' |          Eyes Calibration Complete                                          |')
            self.logger.info(f' |          EAR Threshold: {self.eye_threshold:.3f}                                    |')
            self.logger.info(' └─────────────────────────────────────────────────────────────────────────────┘')

            # 시각화
            self.plot_ear_threshold_graph()
        return self.eye_threshold

    # -----------------------------
    #  상태 전이 함수
    # -----------------------------
    def update_eye_state(self, ear_avg):
        now = time.time()

        if self.eye_state == "none":
            if ear_avg < self.lower_threshold:
                if self.closed_start_time is None:
                    self.closed_start_time = now
                elif now - self.closed_start_time >= self.closed_duration_threshold:
                    self.eye_state = "closed"
                    self.closed_start_time = None
                    self.open_start_time = None
            else:
                self.closed_start_time = None
 
        elif self.eye_state == "closed":
            if ear_avg > self.upper_threshold:
                if self.open_start_time is None:
                    self.open_start_time = now
                elif now - self.open_start_time >= self.open_duration_threshold:
                    self.eye_state = "opened"
                    self.open_start_time = None
                    self.closed_start_time = None
                    self.setting_time = now
            else:
                self.open_start_time = None
        
        elif self.eye_state == "opened" and self.setting_time is not None:
            if now - self.setting_time > self.setting_time_threshold :
                self.eye_state = "none"
                self.setting_time = None
            # else:
            #     self.eye_state ="none"


        return self.eye_state

    # -----------------------------
    #  시각화 함수
    # -----------------------------
    def plot_ear_threshold_graph(self):
        x_vals = list(range(len(self.ear_values)))
        fig = go.Figure()

        # EAR 값들 (초록색 점)
        fig.add_trace(go.Scatter(
            x=x_vals, y=self.ear_values, mode='markers', name='EAR 값',
            marker=dict(color='green', size=6)
        ))

        # Lower Mean (하늘색 점선)
        if self.closed_mean is not None:
            fig.add_trace(go.Scatter(
                x=x_vals, y=[self.closed_mean] * len(self.ear_values),
                mode='lines', name='감은 상태 평균 (Lower)',
                line=dict(color='#00bfff', dash='dot')
            ))

        # Upper Mean (핑크 점선)
        if self.opened_mean is not None:    
            fig.add_trace(go.Scatter(
                x=x_vals, y=[self.opened_mean] * len(self.ear_values),
                mode='lines', name='뜬 상태 평균 (Upper)',
                line=dict(color='#ffb6c1', dash='dot')
            ))

        # Final Threshold (검은 점선)
        if self.eye_threshold is not None:
            fig.add_trace(go.Scatter(
                x=x_vals, y=[self.eye_threshold] * len(self.ear_values),
                mode='lines', name='중간 임계값)',
                line=dict(color='black', dash='dot')
            ))

        # Lower Threshold (파란 점선)
        if self.lower_threshold is not None:
            fig.add_trace(go.Scatter(
                x=x_vals, y=[self.lower_threshold] * len(self.ear_values),
                mode='lines', name='감은 상태 임계값 (Lower)',
                line=dict(color='blue', dash='dash')
            ))

        # Upper Threshold (빨간 점선)
        if self.upper_threshold is not None:    
            fig.add_trace(go.Scatter(
                x=x_vals, y=[self.upper_threshold] * len(self.ear_values),
                mode='lines', name='뜬 상태  임계값 (Upper)',
                line=dict(color='red', dash='dash')
            ))

        fig.update_layout(
            title='EAR Calibration 결과 시각화',
            xaxis_title='프레임 인덱스',
            yaxis_title='EAR 값',
            template='plotly_white',
            height=500
        )
        fig.show()

def main(args=None):
    rclpy.init(args=args)
    node = EyeDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
