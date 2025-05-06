import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import firebase_admin
from firebase_admin import credentials, firestore
import os



class FirebaseBridgeNode(Node):
    def __init__(self):
        super().__init__('status_upload_node')

        # 키 파일 경로
        key_path = os.path.expanduser('~/workspace/ws_drowsiness/firebase-key.json')

        #  Firebase 초기화 코드 추가
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

        # 현재 이메일을 저장하는 변수
        self.current_email = None
        self.active = False
        self.prev_drowsiness_status = None  
        self.prev_yawn_status = None

        self.subscription_email = self.create_subscription(
            String,
            '/current_email',
            self.email_callback,
            10
        )
        self.subscription = self.create_subscription(
            String,
            '/yawn/status',
            self.yawn_status_callback,
            10
        )
        self.subscription = self.create_subscription(
            String,
            '/drowsiness/status',
            self.drowsiness_status_callback,
            10
        )

        self.get_logger().info(' ┌───────────────────────────────────────────────┐')
        self.get_logger().info(' |             Status Upload Node Started        |')
        self.get_logger().info(' └───────────────────────────────────────────────┘')

    def email_callback(self, msg):
        raw_email = msg.data

        #  prefix 파싱
        if raw_email.startswith("[drowsy]"):
            self.active = True
            self.current_email = raw_email.replace("[drowsy]", "")
        
        else:
            self.active = False
            self.current_email = None
            self.get_logger().info(' ┌────────────────────────────────────────────────────────────────┐')
            self.get_logger().info(' |            [drowsy] prefix 없음 → Firebase upload 비활성화        |')
            self.get_logger().info(' └────────────────────────────────────────────────────────────────┘')

    def yawn_status_callback(self, msg):
        if not self.active or not self.current_email:
            self.get_logger().warn("───────────────────────────── 이메일 정보 없음 -> 상태 저장 건너뜀 ─────────────────────────────")
            return
        
        state = msg.data

        # 상태가 이전과 같음 → 아무것도 하지 않음
        if self.prev_yawn_status == state:
            return
        
        # 상태 변경됨 → Firebase 업로드 & 터미널 출력 & 상태 업데이트
        self.prev_yawn_status = state 

        try:
            self.db.collection('users').document(self.current_email).set({
                'yawn status': state
            }, merge=True)
            # self.get_logger().info(' ┌─────────────────────────────────────────────────────────────────────────┐')
            # self.get_logger().info(f" |  하품 상태 '{state}' \n Firebase에 업로드 완료 \n 사용자 : {self.current_email})  |")
            # self.get_logger().info(' └─────────────────────────────────────────────────────────────────────────┘')
            self.get_logger().info(' ┌─────────────────────────────────────────────────────────────────────────┐')
            self.get_logger().info(f" |  하품 상태 '{state}' ")
            self.get_logger().info(' └─────────────────────────────────────────────────────────────────────────┘')

        except Exception as e:
            self.get_logger().error(f"───────────────────────────── Firebase 업로드 실패: {e} ─────────────────────────────")
           
    def drowsiness_status_callback(self, msg):
        if not self.active or not self.current_email:
            self.get_logger().warn("───────────────────────────── 이메일 정보 없음 -> 상태 저장 건너뜀 ─────────────────────────────")
            return

        state = msg.data

        # 상태가 이전과 같음 → 아무것도 하지 않음
        if self.prev_drowsiness_status == state:
            return
        
        # 상태 변경됨 → Firebase 업로드 & 터미널 출력 & 상태 업데이트
        self.prev_drowsiness_status = state 
        
        try:
            self.db.collection('users').document(self.current_email).set({
                'drowsiness status': state
            }, merge=True)
            # self.get_logger().info(' ┌─────────────────────────────────────────────────────────────────────────┐')
            # self.get_logger().info(f" |  졸음 상태 '{state}' \n Firebase에 업로드 완료 \n 사용자 : {self.current_email})  |")
            # self.get_logger().info(' └─────────────────────────────────────────────────────────────────────────┘')
            self.get_logger().info(' ┌─────────────────────────────────────────────────────────────────────────┐')
            self.get_logger().info(f" |  졸음 상태 '{state}' ")
            self.get_logger().info(' └─────────────────────────────────────────────────────────────────────────┘')

        except Exception as e:
            self.get_logger().error(f"───────────────────────────── Firebase 업로드 실패: {e} ─────────────────────────────")
            
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
