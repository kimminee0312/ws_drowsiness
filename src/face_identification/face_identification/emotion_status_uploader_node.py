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
        self.active = False

        self.required_stable_duration = 2.0 # 감정이 2초 이상 유지될 때 업로드
        self.upload_interval = 120.0    # 동일 감정이면 2분마다 업로드

        self.last_emotion_check_time = None
        self.emotion_hold_time = 0.0
        self.emotion_tolerance = 0.2     # 감정 노이즈 무시 허용 시간 (초)

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
            self.get_logger().info("🚫 업로드 비활성화 상태 - UID 없음 또는 active=False")
            return

        emotion_raw = msg.data.strip()
        emotion = emotion_raw.split(" ")[0]
        now = self.get_clock().now().nanoseconds / 1e9  # 초 단위

        if self.last_emotion_check_time is None:
            self.last_emotion_check_time = now

        dt = now - self.last_emotion_check_time
        self.last_emotion_check_time = now

        # 같은 감정일 경우 → 시간 누적
        if emotion == self.current_detected_emotion:
            self.emotion_hold_time += dt

        # 감정이 잠깐 바뀐 경우 (노이즈 허용) → 유지
        elif self.current_detected_emotion and dt < self.emotion_tolerance:
            self.get_logger().info(f"⚠️ 감정 노이즈 무시됨: {self.current_detected_emotion} → {emotion}")
            pass

        # 감정이 명확히 바뀐 경우 → 초기화
        else:
            self.get_logger().info(f"🔁 감정 변경: {self.current_detected_emotion} → {emotion} (초기화)")
            self.current_detected_emotion = emotion
            self.emotion_hold_time = 0.0
            return

        # 감정이 충분히 유지됨
        if self.emotion_hold_time >= self.required_stable_duration:
            should_upload = False

            if self.prev_emotion_status != emotion:
                should_upload = True
            elif self.last_update_time is None or now - self.last_update_time >= self.upload_interval:
                should_upload = True

            if should_upload:
                self.upload_emotion(emotion, now)

    def upload_emotion(self, emotion, now):
        try:
            self.db.collection('users').document(self.current_uid).set({
                'emotion status': emotion
            }, merge=True)
            self.prev_emotion_status = emotion
            self.last_update_time = now
            self.emotion_hold_time = 0.0  # 초기화

            self.get_logger().info(f"🔥 Firebase 업로드 완료: {self.current_uid} → {emotion}")
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