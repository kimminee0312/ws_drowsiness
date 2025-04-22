import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt
import subprocess


class DrowsyGraphGUI(Node):
    def __init__(self):
        super().__init__('drowsy_system_gui_node')

        self.app = QApplication([])
        self.window = QWidget()
        self.layout = QVBoxLayout()

        self.email_label = QLabel("이메일: ❌")
        self.auth_label = QLabel("얼굴 인증 상태: ❌")
        self.graph_label = QLabel("🔄 노드-토픽 연결 정보 확인 중...")
        self.graph_label.setAlignment(Qt.AlignTop)
        self.graph_label.setWordWrap(True)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.graph_label)

        self.layout.addWidget(self.email_label)
        self.layout.addWidget(self.auth_label)
        self.layout.addWidget(scroll_area)

        self.window.setLayout(self.layout)
        self.window.setWindowTitle("Drowsy System Status")
        self.window.resize(500, 600)

        self.create_subscription(String, '/current_email', self.email_callback, 10)
        self.create_subscription(Bool, '/user_authenticated', self.auth_callback, 10)

        self.latest_email = "❌"
        self.latest_auth = False

        self.timer = self.create_timer(2.0, self.update_gui)

    def email_callback(self, msg):
        self.latest_email = msg.data.strip()

    def auth_callback(self, msg):
        self.latest_auth = msg.data

    def get_node_graph_info(self):
        try:
            result = subprocess.run(['ros2', 'node', 'list'], capture_output=True, text=True)
            active_nodes = result.stdout.strip().split('\n')
            active_nodes = [n for n in active_nodes if n]

            # 체크할 주요 노드 목록
            known_nodes = [
                '/fastapi_service_client',

                '/usb_camera_node',
                '/multi_email_service_server_node',

                '/face_register_node',

                '/face_identifier_node',
                '/face_detection_node',
                '/drowsiness_detection_node',
                '/drowsiness_status_upload_node',
            ]

            graph_lines = []

            for node in known_nodes:
                is_active = node in active_nodes
                status = "실행 중" if is_active else "비활성"
                graph_lines.append(f"🟢 [ {node} ]   {status}")

                if is_active:
                    info = subprocess.run(['ros2', 'node', 'info', node], capture_output=True, text=True)
                    current_lines = []
                    display = False

                    for line in info.stdout.splitlines():
                        if 'Publishers:' in line or 'Subscribers:' in line:
                            graph_lines.append(f"  {line.strip()}")
                        elif line.strip().startswith('/'):
                            #  ROS 내부 토픽은 제외
                            if not any(ignore in line for ignore in [
                                'parameter', 'rosout', 'describe_', 'get_', 'set_', 'list_', 
                            ]):
                                current_lines.append(f"    └─ {line.strip()}")
                                display = True
                    
                    if display:
                        graph_lines.extend(current_lines)

                graph_lines.append("")

            return "\n".join(graph_lines)
        except Exception as e:
            return f"❌ 오류 발생: {e}"

    def update_gui(self):
        self.email_label.setText(f"이메일: {self.latest_email}")
        self.auth_label.setText("얼굴 인증 상태: 인증 완료 " if self.latest_auth else "인증 상태: ❌")
        self.graph_label.setText(self.get_node_graph_info())
        self.app.processEvents()


def main(args=None):
    rclpy.init(args=args)
    gui = DrowsyGraphGUI()
    gui.window.show()
    rclpy.spin(gui)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
