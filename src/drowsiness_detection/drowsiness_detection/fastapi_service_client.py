"""
FastAPI 서버에서 ROS 2 서비스 호출
"""

from fastapi import FastAPI
from pydantic import BaseModel
import rclpy
from rclpy.node import Node
import threading
from srv_interfaces.srv import Uid
from srv_interfaces.srv import EndSession 
from rclpy.executors import MultiThreadedExecutor
from time import sleep

app = FastAPI()
rclpy.init()

# =====================================
# ROS 2 서비스 클라이언트 노드 클래스
# =====================================
class FastAPIClientNode(Node):
    def __init__(self):
        super().__init__('fastapi_service_client')

        # 변수명 변경
        self.service_clients = {
            'face_register_service': self.create_client(Uid, 'face_register_service'),
            'start_drowsiness_service': self.create_client(Uid, 'start_drowsiness_service'),
            'end_drowsiness_service': self.create_client(EndSession, 'end_drowsiness_service'),
        }

    def call_service(self, service_name: str, uid: str):
        if service_name not in self.service_clients:
            self.get_logger().error(f"[!] Unknown service: {service_name}")
            return None

        client = self.service_clients[service_name]
        req = Uid.Request()
        req.uid = uid
        future = client.call_async(req)

        while not future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
            sleep(0.1)
        return future.result()

# =====================================
# FastAPI 서버 설정
# =====================================
node = FastAPIClientNode()
threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

executor = MultiThreadedExecutor()
executor.add_node(node)
threading.Thread(target=executor.spin, daemon=True).start()
# FastAPI 모델
class UidModel(BaseModel):
    uid: str

@app.post("/face_register")
def face_register(data: UidModel):
    response = node.call_service("face_register_service", data.uid)
    return {"status": "face_register sent", "ros_response": str(response)}

@app.post("/start_drowsiness")
def start_drowsiness(data: UidModel):
    response = node.call_service("start_drowsiness_service", data.uid)
    return {"status": "start_drowsiness sent", "ros_response": str(response)}

@app.post("/end_drowsiness")
def end_drowsiness(data: UidModel):
    response = node.call_service("end_drowsiness_service", data.uid)
    return {"status": "end_drowsiness sent", "ros_response": str(response)}

