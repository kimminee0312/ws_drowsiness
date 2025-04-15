# ✅ FastAPI 서버에서 ROS 2 서비스 호출

from fastapi import FastAPI
from pydantic import BaseModel
import rclpy
from rclpy.node import Node
import threading
from srv_interfaces.srv import Email


app = FastAPI()
rclpy.init()

# ROS 2 노드 선언
class FastAPIClientNode(Node):
    def __init__(self):
        super().__init__('fastapi_service_client')
        self.cli = self.create_client(Email, 'email_service')  # 서비스 이름
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('서비스 대기 중...')

    def call_service(self, email: str):
        req = Email.Request()
        req.email = email  # 이메일은 service definition에 맞게 custom 타입 쓰면 좋음
        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

node = FastAPIClientNode()
threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

# FastAPI 모델
class EmailModel(BaseModel):
    email: str

@app.post("/email")
def send_email_to_ros(data: EmailModel):
    response = node.call_service(data.email)
    return {"status": "sent", "ros_response": str(response)}
