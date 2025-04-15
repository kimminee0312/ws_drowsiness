# email_server.py (FastAPI 서버)

from fastapi import FastAPI
from pydantic import BaseModel
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading

app = FastAPI()

# ROS 2 노드 선언
class EmailPublisher(Node):
    def __init__(self):
        super().__init__('email_publisher_node')
        self.email_publisher = self.create_publisher(String, '/current_email', 10)
        self.get_logger().info("====== Email Publisher Node started ======")

    def publish_email(self, email: str):
        msg = String()
        msg.data = email
        self.email_publisher.publish(msg)
        self.get_logger().info(f"====== 이메일 publish 완료: {email} ======")

# ROS 2 초기화
rclpy.init()
ros_node = EmailPublisher()

# ROS spin은 별도 스레드에서 실행
threading.Thread(target=rclpy.spin, args=(ros_node,), daemon=True).start()

# FastAPI 입력 모델
class EmailModel(BaseModel):
    email: str

# FastAPI 엔드포인트
@app.post("/email")
def receive_email(data: EmailModel):
    ros_node.publish_email(data.email)
    return {"status": "success", "email": data.email}
