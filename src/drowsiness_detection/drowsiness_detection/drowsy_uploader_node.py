import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime, timedelta
from srv_interfaces.srv import EndSession

class SessionUploaderNode(Node):
    def __init__(self):
        super().__init__('drowsy_uploader_node')

        key_path = os.path.expanduser('~/workspace/ws_drowsiness/firebase-key.json')
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

        self.current_uid = None
        self.session_start = None
        self.session_id = None
        self.active = False

        # 기록할 정보 초기화
        self.blink_count = 0
        self.yawn_count = 0
        self.yawn_durations = []
        self.current_yawn_start = None
        self.closed_periods = []
        self.eye_state = "none"
        self.eye_closed_start = None

        # 구독자 설정
        self.create_subscription(String, '/current_uid', self.uid_callback, 10)
        self.create_subscription(String, '/eyes/status', self.eyes_callback, 10)
        self.create_subscription(String, '/yawn/status', self.yawn_callback, 10)

        self.end_session_srv = self.create_service(EndSession, 'end_drowsiness_service', self.handle_end_session)



        self.get_logger().info(' ┌───────────────────────────────────────────────┐')
        self.get_logger().info(' |             Drowsy Upload Node Started        |')
        self.get_logger().info(' └───────────────────────────────────────────────┘')

    def handle_end_session(self, request, response):
        self.get_logger().info(f"[📩 FastAPI] end_drowsiness_service 요청 수신됨: {request.uid}")

        if self.current_uid == request.uid and self.active:
            self.end_session()
            response.success = True
        else:
            response.success = False
        return response
    
    def uid_callback(self, msg):
        raw = msg.data
        if raw.startswith('[drowsy]'):
            self.current_uid = raw.replace('[drowsy]', '')
            self.session_start = datetime.now()
            self.session_id = self.session_start.strftime('%H_%M_%S')
            self.active = True
            self.get_logger().info(f'[세션 시작] UID: {self.current_uid}, 시작 시간: {self.session_start.strftime("%H:%M:%S")}')
        else:
            self.end_session()

    # 눈 감김 횟수 및 지속 시간(시간시간 포함) 저장 
    def eyes_callback(self, msg):
        if not self.active:
            return

        now = datetime.now()
        state = msg.data

        if state == 'closed' and self.eye_closed_start is None:
            self.eye_closed_start = now

        elif state == 'opened' and self.eye_closed_start:
            duration = now - self.eye_closed_start
            self.closed_periods.append((self.eye_closed_start, duration))
            self.blink_count += 1
            self.eye_closed_start = None

    # 눈 감김(졸음) 피크 시간 계산 함수 
    def compute_peak_drowsy_time(self):
        if not self.closed_periods:
            return "없음"
        peak = max(self.closed_periods, key=lambda x: x[1])
        return peak[0].strftime('%H:%M')

    # 하품 횟수 및 지속 시간 저장 
    def yawn_callback(self, msg):
        if not self.active:
            return

        now = datetime.now()
        state = msg.data

        if "Yawn" in state and self.current_yawn_start is None:
            self.current_yawn_start = now

        elif state == "Normal" and self.current_yawn_start is not None:
            duration = (now - self.current_yawn_start).total_seconds()
            self.yawn_durations.append(duration)
            self.yawn_count += 1
            self.current_yawn_start = None

    # 평균 하품 시간 계산 함수
    def compute_avg_yawn_time(self):
        if not self.yawn_durations:
            return 0.0
        return round(sum(self.yawn_durations) / len(self.yawn_durations), 2)

    # 피로도 점수 계산 함수
    def calculate_fatigue_score(self):
        base_score = 0

        if len(self.yawn_durations) <= 3:
            return base_score

        # 4번째 하품부터 각 초를 감점
        penalties = [round(d.total_seconds()) for d in self.yawn_durations[3:]]
        penalty_sum = sum(penalties)

        fatigue_score = max(0, base_score + penalty_sum)
        return fatigue_score
    
    def calculate_safe_score(self):
        eye_base = 80
        yawn_base = 20

        # 눈 감김 감점 계산
        eye_penalty = 0
        for _, duration in self.closed_periods:
            seconds = duration.total_seconds()
            if seconds < 1.0:
                penalty = 0
            elif seconds < 2.0:
                penalty = 2
            elif seconds < 3.0:
                penalty = 4
            else:
                penalty = 8
            eye_penalty += penalty

        # 하품 감점 계산 (4번째 이후 하품만 감점)
        yawn_penalty = 0
        if len(self.yawn_durations) > 3:
            penalties = [int(d) for d in self.yawn_durations[3:]]  # 초 단위로 반올림
            yawn_penalty = sum(penalties)

        # 감점 적용
        eye_score = max(0, eye_base - eye_penalty)
        yawn_score = max(0, yawn_base - yawn_penalty)

        total_score = eye_score + yawn_score  # 100점 만점

        return total_score

    def end_session(self):
        if not self.active or self.current_uid is None or self.session_start is None:
            return

        end_time = datetime.now()
        duration = end_time - self.session_start
        session_data = {
            'start_time': self.session_start.strftime('%H:%M:%S'),
            'end_time': end_time.strftime('%H:%M:%S'),
            'drowsy_eye_closed': self.blink_count,
            'yawns': self.yawn_count,
            'avg_yawn_duration': round(self.compute_avg_yawn_time(), 2),
            'peak_drowsy_time': self.compute_peak_drowsy_time(),
            'fatigue_score': self.calculate_fatigue_score(),
            'safe_score': self.calculate_safe_score()
        }

        self.get_logger().info(f'[DEBUG] 저장할 데이터: {session_data}')
        self.get_logger().info(f'[DEBUG] UID: "{self.current_uid}", Date: {self.session_start.strftime("%Y-%m-%d")}, SessionID: {self.session_id}')


        try:
            today = self.session_start.strftime('%Y-%m-%d')
            doc_ref = self.db.collection('users').document(self.current_uid)                .collection('DrowsyData').document(today)                .collection('Sessions').document(self.session_id)
            doc_ref.set(session_data)
            self.get_logger().info(f'✅ 세션 업로드 완료: {today}/{self.session_id}')
        except Exception as e:
            self.get_logger().error(f'❌ 업로드 실패: {e}')

        # 초기화
        self.active = False
        self.current_uid = None
        self.session_start = None
        self.session_id = None
        self.blink_count = 0
        self.yawn_count = 0
        self.yawn_durations = []
        self.current_yawn_start = None
        self.closed_periods = []
        self.eye_state = "none"
        self.eye_closed_start = None

def main(args=None):
    rclpy.init(args=args)
    node = SessionUploaderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("KeyboardInterrupt 발생: 세션 종료 및 데이터 저장 시도 중...")
        node.end_session()  # Firestore 저장까지 확실히 끝내고 종료하도록 함
    finally:
        # shutdown은 end_session 이후에만 안전하게 실행
        rclpy.shutdown()

if __name__ == '__main__':
    main()