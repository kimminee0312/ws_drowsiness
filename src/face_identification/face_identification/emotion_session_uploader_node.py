import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import os
from srv_interfaces.srv import EndSession


class EmotionSessionUploaderNode(Node):
    def __init__(self):
        super().__init__('emotion_session_uploader_node')

        # Firebase 인증
        key_path = os.path.expanduser('~/workspace/ws_drowsiness/firebase-key.json')
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

        # 상태 변수 초기화
        self.current_uid = None
        self.session_start = None
        self.session_id = None
        self.active = False
        self.current_emotion = None
        self.prev_time = None

        self.durations = {
            'positive': 0.0,
            'neutral': 0.0,
            'negative': 0.0
        }

        # 구독 및 서비스
        self.create_subscription(String, '/current_uid', self.uid_callback, 10)
        self.create_subscription(String, '/emotion/status', self.emotion_callback, 10)
        self.create_service(EndSession, 'end_emotion_service', self.end_session_callback)

        self.get_logger().info('🧠 Emotion Uploader Node Started')

    def uid_callback(self, msg):
        raw = msg.data
        if raw.startswith('[emotion]'):
            self.current_uid = raw.replace('[emotion]', '')
            if self.active:
                self.get_logger().warn(f"이미 감정 세션 진행 중 → 새 요청 무시: {self.current_uid}")
                return

            self.session_start = datetime.now()
            self.session_id = self.session_start.strftime('%H_%M_%S')
            self.prev_time = self.session_start
            self.active = True

            self.durations = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
            self.current_emotion = None

            self.get_logger().info(f"✅ 감정 세션 시작: {self.session_start.strftime('%H:%M:%S')}")

    def emotion_callback(self, msg):
        if not self.active:
            return

        try:
            label = msg.data.strip()
            now = datetime.now()

            if self.current_emotion and self.prev_time:
                delta = (now - self.prev_time).total_seconds()
                self.durations[self.current_emotion] += delta

            self.current_emotion = label
            self.prev_time = now
        except Exception as e:
            self.get_logger().error(f"⚠️ 감정 메시지 파싱 실패: {e}")

    def end_session_callback(self, request, response):
        if self.active:
            self.end_session()
            response.success = True
        else:
            response.success = False
        return response

    def end_session(self):
        if not self.active or not self.current_uid:
            return

        end_time = datetime.now()

        # 마지막 감정 누적
        if self.current_emotion and self.prev_time:
            delta = (end_time - self.prev_time).total_seconds()
            self.durations[self.current_emotion] += delta

        total = sum(self.durations.values())
        if total == 0:
            score = 0
        else:
            positive_ratio = self.durations['positive'] / total
            negative_ratio = self.durations['negative'] / total
            score = 70 + int(positive_ratio * 30) - int(negative_ratio * 30)
            score = max(0, min(score, 100))  # 0~100 범위 제한

        summary = max(self.durations.items(), key=lambda x: x[1])[0]

        session_data = {
            'start_time': self.session_start.strftime('%H:%M:%S'),
            'end_time': end_time.strftime('%H:%M:%S'),
            'positive_duration': round(self.durations['positive'], 1),
            'neutral_duration': round(self.durations['neutral'], 1),
            'negative_duration': round(self.durations['negative'], 1),
            'emotion_score': score,
            'emotion_summary': summary
        }

        try:
            today = self.session_start.strftime('%Y-%m-%d')
            doc = self.db.collection('users') \
                         .document(self.current_uid) \
                         .collection('EmotionData') \
                         .document(today)

            doc.set({'latest': firestore.SERVER_TIMESTAMP}, merge=True)
            doc.collection('Sessions').document(self.session_id).set(session_data)

            self.get_logger().info(f"📦 감정 세션 업로드 완료: {today}/{self.session_id}")
            self.get_logger().info(f"📝 저장 데이터: {session_data}")
        except Exception as e:
            self.get_logger().error(f"❌ Firebase 업로드 실패: {e}")

        # 초기화
        self.active = False
        self.session_start = None
        self.session_id = None
        self.current_uid = None
        self.current_emotion = None
        self.prev_time = None
        self.durations = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}

def main(args=None):
    rclpy.init(args=args)
    node = EmotionSessionUploaderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node.active:
            node.end_session()
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()