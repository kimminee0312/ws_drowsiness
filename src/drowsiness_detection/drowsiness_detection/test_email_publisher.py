import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool

class TestEmailPublisher(Node):
    def __init__(self):
        super().__init__('test_email_publisher')

        # 이메일 발행 퍼블리셔
        self.email_pub = self.create_publisher(String, '/current_email', 10)

        # 인증 상태 퍼블리셔
        self.auth_pub = self.create_publisher(Bool, '/user_authenticated', 10)

        # 타이머: 2초 간격으로 발행
        self.timer = self.create_timer(2.0, self.timer_callback)

        # 고정 이메일 (테스트용)
        self.test_email = '[drowsy]kimminee9349@gmail.com'

        self.get_logger().info('✅ TestEmailPublisher Node Started')

    def timer_callback(self):
        # 이메일 메시지 발행
        email_msg = String()
        email_msg.data = self.test_email
        self.email_pub.publish(email_msg)
        self.get_logger().info(f'📤 Published Email: {email_msg.data}')

        # 인증 메시지 발행 (항상 True)
        auth_msg = Bool()
        auth_msg.data = True
        self.auth_pub.publish(auth_msg)
        self.get_logger().info('📤 Published Authenticated: True')

def main(args=None):
    rclpy.init(args=args)
    node = TestEmailPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
