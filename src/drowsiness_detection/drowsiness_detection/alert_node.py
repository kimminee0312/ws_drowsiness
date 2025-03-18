import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class AlertNode(Node):
    def __init__(self):
        super().__init__('alert_node')
        self.subscription = self.create_subscription(String, '/drowsiness/status', self.status_callback, 10)
        self.get_logger().info("🚨 Alert Node Started ✅")

    def status_callback(self, msg):
        if msg.data.startswith("Drowsy"):
            self.get_logger().warn(f"⚠️ ALERT! {msg.data}")

def main(args=None):
    rclpy.init(args=args)
    node = AlertNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
