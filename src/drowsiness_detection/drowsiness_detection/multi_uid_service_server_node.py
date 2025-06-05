"""
email_service_server.py
ROS 2 서비스 서버: 이메일 요청 받으면 /current_uid 토픽 발행
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from srv_interfaces.srv import Uid 

class MultiUidServiceNode(Node):
    def __init__(self):
        super().__init__('multi_uid_service_server_node')

        # publisher
        self.uid_publisher = self.create_publisher(String, '/current_uid', 10)

        # service 서버 생성
        self.face_srv = self.create_service(Uid, 'face_register_service', self.face_callback)

        self.drowy_start_srv = self.create_service(Uid, 'start_drowsiness_service', self.drowy_start_callback)

        self.emotion_start_srv = self.create_service(Uid, 'start_emotion_service', self.emotion_start_callback)
        
        self.get_logger().info(' ┌────────────────────────────────────────────┐')
        self.get_logger().info(' |       Multi uid service server start       |')
        self.get_logger().info(' └────────────────────────────────────────────┘')


    def face_callback(self, request, response):
        uid = request.uid
        uid_msg = String()
        uid_msg.data = uid

        self.uid_publisher.publish(uid_msg)
        self.get_logger().info(f'uid pub to face register: {uid}')

        response.success = True
        response.message = 'face_register_service completion'
        return response

    def drowy_start_callback(self, request, response):
        uid = request.uid
        uid_msg = String()
        uid_msg.data = uid

        self.uid_publisher.publish(uid_msg)
        self.get_logger().info(f'uid pub to start drowsiness detector: {uid}')

        response.success = True
        response.message = 'start_drowsiness_service completion'
        return response
    
    def emotion_start_callback(self, request, response):
        uid = request.uid
        uid_msg = String()
        uid_msg.data = uid

        self.uid_publisher.publish(uid_msg)
        self.get_logger().info(f'uid pub to start emotion detector: {uid}')

        response.success = True
        response.message = 'start_emotion_service completion'
        return response
    
def main(args=None):
    rclpy.init(args=args)
    node = MultiUidServiceNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
