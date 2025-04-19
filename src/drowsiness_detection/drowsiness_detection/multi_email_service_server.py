# email_service_server.py
# ROS 2 서비스 서버: 이메일 요청 받으면 /current_email 토픽 발행

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from srv_interfaces.srv import Email 

class MultiEmailServiceNode(Node):
    def __init__(self):
        super().__init__('multi_email_service_node')

        # publisher
        self.email_publisher = self.create_publisher(String, '/current_email', 10)

        # service 서버 생성
        self.face_srv = self.create_service(Email, 'face_register_service', self.face_callback)

        self.drowy_srv = self.create_service(Email, 'start_drowsiness_service', self.drowy_callback)

        self.get_logger().info(' ┌────────────────────────────────────────────┐')
        self.get_logger().info(' |       Multi email service server start     |')
        self.get_logger().info(' └────────────────────────────────────────────┘')


    def face_callback(self, request, response):
        email = request.email
        email_msg = String()
        email_msg.data = email

        self.email_publisher.publish(email_msg)
        self.get_logger().info(f'Email pub to face register: {email}')

        response.success = True
        response.message = 'face_register_service completion'
        return response

    def drowy_callback(self, request, response):
        email = request.email
        email_msg = String()
        email_msg.data = email

        self.email_publisher.publish(email_msg)
        self.get_logger().info(f'Email pub to start drowsiness: {email}')

        response.success = True
        response.message = 'start_drowsiness_service completion'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = MultiEmailServiceNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
