"""
백파일과 졸음 알고리즘 실행 후 예측 상채 csv 파일로 저장 스크립트
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
# from builtin_interfaces.msg import Time as RosTime
# import rosgraph_msgs as RosTime 
from rosgraph_msgs.msg import Clock as RosTime
from rclpy.qos import QoSProfile, ReliabilityPolicy
import csv
import argparse
import time
import os
from pathlib import Path

class PredictionLogger(Node):
    def __init__(self, topic_name, output_path):
        super().__init__('prediction_logger_node')

        qos_best_effort = QoSProfile(depth=10)
        qos_best_effort.reliability = ReliabilityPolicy.BEST_EFFORT

        self.prev_status = None
        self.latest_clock = None  # 최신 /clock 시간 저장용

        # 상태 토픽 구독
        self.subscription = self.create_subscription(
            String,
            topic_name,
            self.listener_callback,
            10)

        # /clock 토픽 구독
        self.clock_sub = self.create_subscription(
            RosTime,
            '/clock',
            self.clock_callback,
            qos_profile=qos_best_effort)

        # 파일 및 경로 설정
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        self.file = open(output_path, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(["timestamp", "status"])

    def clock_callback(self, msg):
        self.latest_clock = msg

    def listener_callback(self, msg):
        current_status = msg.data.lower()
        if current_status != self.prev_status and self.latest_clock is not None:
            timestamp = self.latest_clock.clock.sec + self.latest_clock.clock.nanosec * 1e-9
            self.writer.writerow([timestamp, current_status])
            self.get_logger().info(f"Logged: {current_status} at {timestamp}")
            self.prev_status = current_status

    def destroy_node(self):
        self.file.close()
        super().destroy_node()

def main(args=None):
    parser = argparse.ArgumentParser(description="ROS2 Topic-based Prediction Logger using /clock time")
    parser.add_argument("--topic", required=True, help="ROS2 topic to subscribe (e.g. /eyes/status)")
    parser.add_argument("--output", required=True, help="Relative path from ./performance_evaluation/")
    args = parser.parse_args()

    rclpy.init()
    base_path = "/home/kml/workspace/ws_drowsiness/performance_evaluation"
    full_output_path = os.path.join(base_path, args.output)

    prediction_logger = PredictionLogger(args.topic, full_output_path)

    try:
        rclpy.spin(prediction_logger)
    except KeyboardInterrupt:
        pass
    finally:
        prediction_logger.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
