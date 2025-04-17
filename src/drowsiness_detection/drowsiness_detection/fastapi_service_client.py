# ✅ FastAPI 서버에서 ROS 2 서비스 호출

from fastapi import FastAPI
from pydantic import BaseModel
import rclpy
from rclpy.node import Node
import threading
from srv_interfaces.srv import Email


app = FastAPI()
rclpy.init()

# =====================================
# ROS 2 서비스 클라이언트 노드 클래스
# =====================================
class FastAPIClientNode(Node):
    def __init__(self):
        super().__init__('fastapi_service_client')
        # 서비스 클라이언트들을 딕셔너리로 관리
        self._clients = {
            'face_register_service' : self.create_client(Email, 'face_register_service'),
            'start_drowsiness_service' : self.create_client(Email,'start_drowsiness_service'),
        }

        for name, client in self._clients.items():
            while not client.wait_for_service(timeout_sec=1.0):
                self.get_logger().info(f"─────────────────────── 서비스 '{name}' 대기 중... ───────────────────────")

    def call_service(self, service_name: str, email: str):
        if service_name not in self._clients:
            self.get_logger().error(f" ──────────────────────── 존재하지 않는 서비스 요청: {service_name} ───────────────────────")
            return None
        
        clients = self._clients[service_name]
        req = Email.Request()
        req.email = email 

        future = clients.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

# =====================================
# FastAPI 서버 설정
# =====================================
node = FastAPIClientNode()
threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

# FastAPI 모델
class EmailModel(BaseModel):
    email: str

@app.post("/face_register")
def face_register(data: EmailModel):
    response = node.call_service("face_register_service", data.email)
    return {"status": "face_register sent", "ros_response": str(response)}

@app.post("/start_drowsiness")
def start_drowsiness(data: EmailModel):
    response = node.call_service("start_drowsiness_service", data.email)
    return {"status": "start_drowsiness sent", "ros_response": str(response)}
