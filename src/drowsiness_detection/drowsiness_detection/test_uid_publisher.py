"""
졸음 인식 알고리즘 수정하고 확인 할 때 앱 연동 하기 귀찮아서 
자동으로 uid랑 얼굴 식별 확인 결과 토픽 발행 해주는 스크립트 
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool

class TestUidPublisher(Node):
    def __init__(self):
        super().__init__('test_uid_publisher')

        # 이메일 발행 퍼블리셔
        self.uid_pub = self.create_publisher(String, '/current_uid', 10)

        # 인증 상태 퍼블리셔
        self.auth_pub = self.create_publisher(Bool, '/user_authenticated', 10)

        # 타이머: 2초 간격으로 발행
        self.timer = self.create_timer(2.0, self.timer_callback)

        # 고정 이메일 (테스트용)
        self.test_uid = '[drowsy]8YL5MDuor2XiEJKIF61xMApJtEm2'

        self.get_logger().info('✅ TestUidPublisher Node Started')

    def timer_callback(self):
        # 이메일 메시지 발행
        uid_msg = String()
        uid_msg.data = self.test_uid
        self.uid_pub.publish(uid_msg)
        self.get_logger().info(f'📤 Published Uid: {uid_msg.data}')

        # 인증 메시지 발행 (항상 True)
        auth_msg = Bool()
        auth_msg.data = True
        self.auth_pub.publish(auth_msg)
        self.get_logger().info('📤 Published Authenticated: True')

def main(args=None):
    rclpy.init(args=args)
    node = TestUidPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
