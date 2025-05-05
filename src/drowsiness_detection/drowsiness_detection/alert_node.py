import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class AlertNode(Node):
    def __init__(self):
        super().__init__('alert_node')

        self.yawn_status = "Normal"
        self.drowsy_status = "Normal"

        self.subscription = self.create_subscription(
            String, 
            '/yawn/status',
            self.yawn_callback, 
            10)
        
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

    def yawn_callback(self, msg):
        if msg.data.startswith("Yawning"):
            alert_msg = String()
            alert_msg.data = "하품 감지 - 가벼운 스트레칭을 해보세요"
            self.publisher.publish(alert_msg)

    def drowsiness_callback(self, msg):
        if msg.data.startswith("눈 감김"):
            alert_msg = String()
            alert_msg.data = "졸음 감지 - 정면을 주시해 주세요"
            self.publisher.publish(alert_msg)

        elif msg.data.startswith("Normal"):
            alert_msg = String()
            alert_msg.data = "안전운전하세요"
            self.publisher.publish(alert_msg)

def main(args=None):
    rclpy.init(args=args)
    node = AlertNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
