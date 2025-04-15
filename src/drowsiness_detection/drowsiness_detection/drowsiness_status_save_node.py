import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import firebase_admin
from firebase_admin import credentials, firestore
import os

class FirebaseBridgeNode(Node):
    def __init__(self):
        super().__init__('drowsiness_status_save_node')

        # 키 파일 경로
        key_path = os.path.expanduser('~/workspace/ws_drowsiness/firebase-key.json')


        # 현재 이메일을 저장하는 변수
        self.current_email = None

        # ROS 구독
        self.subscription_email = self.create_subscription(
            String,
            '/current_email',
            self.email_callback,
            10
        )

        # ROS 2 구독 설정
        self.subscription = self.create_subscription(
            String,
            '/drowsiness/status',
            self.status_callback,
            10
        )

        self.get_logger().info("====== Drowsiness Status Save Node Started ======")

    def email_callback(self, msg):
        self.current_email = msg.data
        self.get_logger().info(f"====== 현재 사용자 이메일 저장: {self.current_email} ======")

    def status_callback(self, msg):
        if not self.current_email:
            self.get_logger().warn("====== 이메일 정보 없음 -> 상태 저장 건너뜀 ======")
            return

        state = msg.data
        try:
            self.db.collection('users').document(self.current_email).set({
                'state': state
            }, merge=True)
            self.get_logger().info(f"상태 '{state}' \n Firebase에 업로드 완료 \n 유저: {self.current_email})")
        except Exception as e:
            self.get_logger().error(f"====== Firebase 업로드 실패: {e} ======")

def main(args=None):
    rclpy.init(args=args)
    node = FirebaseBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
