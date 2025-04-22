import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import subprocess

class SystemStatusNode(Node):
    def __init__(self):
        super().__init__('drowsy_system_status_node')

        self.current_email = "미수신"
        self.authenticated = False
        self.prev_snapshot = ""

        self.create_subscription(String, '/current_email', self.email_callback, 10)
        self.create_subscription(Bool, '/user_authenticated', self.auth_callback, 10)

        self.timer = self.create_timer(1.0, self.print_status)  # 1초마다 상태 출력

        self.node_descriptions = {
            '/fastapi_service_client': '📘  App → [요청] → ROS Service Server',
            '/usb_camera_node': '📘 USB 카메라 이미지 Pub',
            '/multi_email_service_server_node': '📘 → Service',
            '/face_register_node': '📘 얼굴 등록 ',
            '/face_identifier_node': '📘 얼굴 인증 ',
            '/face_detection_node': '📘 얼굴 인식 ',
            '/drowsiness_detection_node': '📘 졸음 상태 판단',
            '/drowsiness_status_upload_node': '📘 졸음 상태 Firebase 업로드',
        }

    def email_callback(self, msg):
        self.current_email = msg.data.strip()

    def auth_callback(self, msg):
        self.authenticated = msg.data

    def print_status(self):
        try:
            result = subprocess.run(['ros2', 'node', 'list'], capture_output=True, text=True)
            active_nodes = result.stdout.strip().split('\n')
            active_nodes = [n for n in active_nodes if n]

            known_nodes = list(self.node_descriptions.keys())

            snapshot_lines = []
            snapshot_lines.append(' ┌──────────────────────────────────────────────────────────────┐')
            snapshot_lines.append(' |                      시스템 상태 진단 중...                    |')
            snapshot_lines.append(' └──────────────────────────────────────────────────────────────┘')
            snapshot_lines.append(f'     현재 이메일: {self.current_email}')
            snapshot_lines.append(f"     얼굴 인증 상태: {'인증' if self.authenticated else '미인증'}\n")


            for node in known_nodes:
                if node not in active_nodes:
                    snapshot_lines.append(f" ❌ {node} \n ")
                    continue

                snapshot_lines.append(f" ➡️ {node} ")
                desc = self.node_descriptions.get(node)

                if desc:
                    snapshot_lines.append(f"    {desc}")

                info = subprocess.run(['ros2', 'node', 'info', node], capture_output=True, text=True)
                lines = info.stdout.splitlines()

                publishers = []
                subscribers = []
                current_mode = None

                for line in lines:
                    if 'Publishers:' in line:
                        current_mode = 'Pub'
                    elif 'Subscribers:' in line:
                        current_mode = 'Sub'
                    elif line.strip().startswith('/'):
                        topic = line.strip().split(':')[0].strip()
                        # ROS 내부용 토픽 제외
                        if not any(x in topic for x in ['parameter', 'rosout', 'describe_', 'get_', 'set_', 'list_']):
                            if current_mode == 'Pub':
                                publishers.append(topic)
                            elif current_mode == 'Sub':
                                subscribers.append(topic)
                if subscribers:
                    snapshot_lines.append("       Sub :")
                    for topic in subscribers:
                        snapshot_lines.append(f"      └─ {topic}")

                if publishers:
                    snapshot_lines.append("       Pub :")
                    for topic in publishers:
                        snapshot_lines.append(f"      └─ {topic}")

                snapshot_lines.append("")

            snapshot = "\n".join(snapshot_lines)
            if snapshot != self.prev_snapshot:
                self.get_logger().info("\n" + snapshot)
                self.prev_snapshot = snapshot

        except Exception as e:
            self.get_logger().error(f"=================== 노드 상태 확인 중 오류 발생: {e} ===================")

def main(args=None):
    rclpy.init(args=args)
    node = SystemStatusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
