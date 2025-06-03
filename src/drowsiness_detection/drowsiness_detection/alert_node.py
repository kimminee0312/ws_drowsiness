import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class AlertNode(Node):
    def __init__(self):
        super().__init__('alert_node')

        # 눈 감김 이벤트를 셀 때 사용할 변수들
        self.eye_closed_event_count = 0   # distinct 눈 감김 이벤트 횟수
        self.was_eye_closed = False       # 이전 프레임에서 눈이 감겼었는지
        
        self.subscription = self.create_subscription(
            String, 
            '/drowsiness/status',
            self.drowsiness_callback, 
            10)
        
        self.publisher = self.create_publisher(
            String, 
            '/alert', 
            10)

        self.get_logger().info(' ┌────────────────────────────────────────────┐')
        self.get_logger().info(' |               Alert Node Start             |')
        self.get_logger().info(' └────────────────────────────────────────────┘')

    def drowsiness_callback(self, msg: String):
        text = msg.data

        # 1) 캘리브레이션
        if "Calibrating Now" in text:
            alert_msg = String()
            alert_msg.data = "캘리브레이션 중입니다. 카메라를 정면으로 보고 눈을 깜빡여주세요."
            self.publisher.publish(alert_msg)
            self.was_eye_closed = False
            return

        # 2) 하품 감지 (텍스트에 '하품 후보' 또는 '하품 감지'가 포함되면)
        if "하품 후보" in text or "하품 감지" in text:
            alert_msg = String()
            alert_msg.data = "하품이 감지되었습니다."
            self.publisher.publish(alert_msg)
            self.was_eye_closed = False
            return

        # 3) 눈 감김 감지
        if "눈 감김" in text:
            if not self.was_eye_closed:
                self.eye_closed_event_count += 1
                self.was_eye_closed = True

            if self.eye_closed_event_count >= 3:
                alert_msg = String()
                alert_msg.data = (
                    f"눈 감김이 {self.eye_closed_event_count}번 반복되었습니다. 졸음 쉼터로 이동해주세요."
                )
                self.publisher.publish(alert_msg)
            else:
                alert_msg = String()
                alert_msg.data = "위험합니다. 졸음 운전이 감지되었습니다."
                self.publisher.publish(alert_msg)
            return

        # 4) Normal 상태
        if "Normal" in text:
            self.was_eye_closed = False
            alert_msg = String()
            alert_msg.data = "안전운전하세요"
            self.publisher.publish(alert_msg)
            return

        # 5) 그 외
        self.was_eye_closed = False


def main(args=None):
    rclpy.init(args=args)
    node = AlertNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
