import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import firebase_admin
from firebase_admin import credentials, firestore
import os

class EmotionStatusUploaderNode(Node):
    def __init__(self):
        super().__init__('emotion_status_uploader_node')

        key_path = os.path.expanduser('~/workspace/ws_drowsiness/firebase-key.json')
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

        self.current_uid = None
        self.prev_emotion_status = None
        self.current_detected_emotion = None
        self.last_update_time = None
        self.emotion_change_time = None
        self.active = False

        self.required_stable_duration = 3 # 감정이 5초 이상 유지될 때만 인정
        self.upload_interval = 120  # 동일 감정일 경우 2분마다 업로드 허용

        self.create_subscription(String, '/current_uid', self.uid_callback, 10)
        self.create_subscription(String, '/emotion/status', self.emotion_status_callback, 10)

        self.get_logger().info("📡 Emotion Status Uploader Node Started")

    def uid_callback(self, msg):
        raw = msg.data.strip()
        if raw.startswith("[emotion]"):
            self.active = True
            self.current_uid = raw.replace("[emotion]", "").strip()
            self.get_logger().info(f"✅ 감정 UID 수신: {self.current_uid}")
        else:
            self.active = False
            self.current_uid = None
            self.get_logger().info("⚠️ [emotion] prefix 없음 → 업로드 비활성화")

    def emotion_status_callback(self, msg):
        if not self.active or not self.current_uid:
            return

        emotion_raw = msg.data.strip()
        emotion = emotion_raw.split(" ")[0]  
        now = self.get_clock().now().nanoseconds / 1e9  # 초 단위

        if emotion != self.current_detected_emotion:
            self.current_detected_emotion = emotion
            self.emotion_change_time = now
            return

        # 감정 유지 시간 충족 여부
        emotion_stable = self.emotion_change_time and (now - self.emotion_change_time >= self.required_stable_duration)

        should_upload = False
        if self.prev_emotion_status != emotion and emotion_stable:
            should_upload = True
        elif self.prev_emotion_status == emotion:
            if self.last_update_time is None or (now - self.last_update_time >= self.upload_interval):
                should_upload = True

        if should_upload:
            try:
                self.db.collection('users').document(self.current_uid).set({
                    'emotion status': emotion
                }, merge=True)
                self.prev_emotion_status = emotion
                self.last_update_time = now
            except Exception as e:
                self.get_logger().error(f"❌ 업로드 실패: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = EmotionStatusUploaderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()