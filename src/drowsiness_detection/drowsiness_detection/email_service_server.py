# email_service_server.py
# ROS 2 서비스 서버: 이메일 요청 받으면 /current_email 토픽 발행

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from srv_interfaces.srv import Email 

class EmailServiceNode(Node):
    def __init__(self):
        super().__init__('email_service_node')

        # publisher
        self.publisher_ = self.create_publisher(String, '/current_email', 10)

        # service 서버 생성
        self.srv = self.create_service(Email, 'email_service', self.email_callback)
        self.get_logger().info('✅ 이메일 서비스 서버 실행 중')

    def email_callback(self, request, response):
        email_msg = String()
        email_msg.data = request.email
        self.publisher_.publish(email_msg)

        self.get_logger().info(f'📡 이메일 토픽 발행: {request.email}')
        response.success = True
        response.message = '이메일 발행 완료'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = EmailServiceNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
