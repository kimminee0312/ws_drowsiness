"""
raw ear 값이랑 칼만필터 적용한 Kal ear 값 저장 하는 스크립트 
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import csv
import os
from datetime import datetime

class EARLoggerNode(Node):
    def __init__(self):
        super().__init__('ear_logger_node')

        self.raw_ear = None
        self.kalman_ear = None
        self.frame_count = 0

        # ✅ 저장 경로 고정
        log_dir = "/home/kml/workspace/ws_drowsiness/Test_data/raw_kal_ear_csv"
        os.makedirs(log_dir, exist_ok=True)

        # ✅ 파일 이름 자동 생성
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"ear_log_{now}.csv"
        self.log_path = os.path.join(log_dir, file_name)

        self.file = open(self.log_path, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['frame', 'ear_raw', 'ear_kalman'])

        self.create_subscription(Float32, '/debug/ear/raw', self.raw_callback, 10)
        self.create_subscription(Float32, '/debug/ear/kal', self.kalman_callback, 10)

        self.get_logger().info(f"[EAR Logger] 저장 경로: {self.log_path}")

    def raw_callback(self, msg):
        self.raw_ear = msg.data
        self.try_write()

    def kalman_callback(self, msg):
        self.kalman_ear = msg.data
        self.try_write()

    def try_write(self):
        if self.raw_ear is not None and self.kalman_ear is not None:
            self.writer.writerow([self.frame_count, self.raw_ear, self.kalman_ear])
            self.frame_count += 1
            self.raw_ear = None
            self.kalman_ear = None

    def destroy_node(self):
        self.file.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = EARLoggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
