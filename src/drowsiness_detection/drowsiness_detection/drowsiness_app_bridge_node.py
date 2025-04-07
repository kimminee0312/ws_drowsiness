import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import firebase_admin
from firebase_admin import credentials, firestore
import os

class FirebaseBridgeNode(Node):
    def __init__(self):
        super().__init__('drowsiness_app_bridge_node')

        # 키 파일 경로
        key_path = os.path.expanduser('~/workspace/ws_drowsiness/firebase-key.json')

        # Firebase 초기화
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

        # ROS 2 구독 설정
        self.subscription = self.create_subscription(
            String,
            '/drowsiness/status',
            self.status_callback,
            10
        )

        self.get_logger().info("✅ Firebase Bridge Node started!")

    def status_callback(self, msg):
        state = msg.data
        self.get_logger().info(f"📡 상태 수신: {state}")

        # Firestore에 업로드
        try:
            self.db.collection('users').document('test_user').set({'state': state})
            self.get_logger().info("✅ Firebase에 업로드 완료")
        except Exception as e:
            self.get_logger().error(f"❌ Firebase 업로드 실패: {e}")

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
