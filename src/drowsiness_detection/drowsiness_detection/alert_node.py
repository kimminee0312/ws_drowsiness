import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class AlertNode(Node):
    def __init__(self):
        super().__init__('alert_node')
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
        if msg.data.startswith("Yawing"):
            self.get_logger().warn(f"하품 감지됨 - 가벼운 스트레칭을 해보세요!")

    def drowsiness_callback(self, msg):
        if msg.data.startswith("눈 감김"):
            self.get_logger().warn(f"정면을 주시해 주세요")

def main(args=None):
    rclpy.init(args=args)
    node = AlertNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
