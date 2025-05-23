"""
정답 cvs 파일 수기로 작성한 레이블링 따라서 시간 맞춰 토픽 발행 해주는 스크립트 
눈으로 알고리즘 반응 보기 위해서 작성 
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rosgraph_msgs.msg import Clock
import csv
from rclpy.qos import QoSProfile, ReliabilityPolicy

class ClockSyncedLabelPublisher(Node):
    def __init__(self, csv_path='/home/kml/workspace/ws_drowsiness/Test_data/correct_csv/labels1.csv'):
        super().__init__('clock_synced_label_publisher')

        self.csv_path = csv_path

        self.publisher = self.create_publisher(
            String, 
            '/test/drowsiness/status', 
            10)
        
        self.labels = self.load_csv()
        self.next_index = 0

        clock_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            depth=10
        )
        self.subscription = self.create_subscription(
            Clock,
            '/clock',
            self.clock_callback,
            clock_qos
        )
        self.get_logger().info(f"Loaded {len(self.labels)} labels from CSV.")

    def load_csv(self):
        labels = []
        with open(self.csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                timestamp = float(row['timestamp_sec'])
                event = row['event'].strip()
                labels.append((timestamp, event))
        return sorted(labels, key=lambda x: x[0])

    def clock_callback(self, msg: Clock):
        current_time = msg.clock.sec + msg.clock.nanosec * 1e-9

        # 아직 발행할 시점이 안 됐으면 리턴
        if self.next_index >= len(self.labels):
            return

        # 아직 해당 이벤트 시점 도달 안 했으면 아무것도 하지 않음
        if current_time < self.labels[self.next_index][0]:
            return

        # 시점에 도달했거나 지나갔다면 발행
        while self.next_index < len(self.labels) and current_time >= self.labels[self.next_index][0]:
            timestamp, event = self.labels[self.next_index]
            msg_out = String()
            msg_out.data = event
            self.publisher.publish(msg_out)
            self.get_logger().info(f"[{timestamp:.3f}] Published: {event}")
            self.next_index += 1



def main(args=None):
    rclpy.init(args=args)
    node = ClockSyncedLabelPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
