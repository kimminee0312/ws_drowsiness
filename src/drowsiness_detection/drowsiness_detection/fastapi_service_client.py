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
        self.uid_clients = {
            'face_register_service': self.create_client(Uid, 'face_register_service'),
            'start_drowsiness_service': self.create_client(Uid, 'start_drowsiness_service'),
            'start_emotion_service': self.create_client(Uid, 'start_emotion_service'),

        }

        self.end_session_client = self.create_client(EndSession, 'end_drowsiness_service')

    # ───────────────────────────────────────────────────
    # Uid 타입 서비스 호출 (email/uid 필요)
    # ───────────────────────────────────────────────────
    def call_uid_service(self, service_name: str, uid: str):
        if service_name not in self.uid_clients:
            self.get_logger().error(f"[!] Unknown service: {service_name}")
            return None

        client = self.uid_clients[service_name]

        if not client.wait_for_service(timeout_sec=2.0):
            self.get_logger().error(f"[!] {service_name} is not available")
            return None

        req = Uid.Request()
        req.uid = uid

        future = client.call_async(req)

        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        if future.done():
            return future.result()
        else:
            self.get_logger().error(f"[!] {service_name} timed out")
            return None

    # ───────────────────────────────────────────────────
    # EndSession 타입 서비스 호출 (입력 없이 호출)
    # ───────────────────────────────────────────────────
    def call_end_service(self):
        client = self.end_session_client

        if not client.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("[!] end_drowsiness_service is not available")
            return None

        req = EndSession.Request()

        future = client.call_async(req)

        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        if future.done():
            return future.result()
        else:
            self.get_logger().error("[!] end_drowsiness_service timed out")
            return None

# =====================================
# FastAPI 서버 설정
# =====================================
node = FastAPIClientNode()

executor = MultiThreadedExecutor()
executor.add_node(node)
threading.Thread(target=executor.spin, daemon=True).start()
# FastAPI 모델
class UidModel(BaseModel):
    uid: str

@app.post("/face_register")
def face_register(data: UidModel):
    response = node.call_uid_service("face_register_service", data.uid)
    return {"status": "face_register sent", "ros_response": str(response)}

@app.post("/start_drowsiness")
def start_drowsiness(data: UidModel):
    response = node.call_uid_service("start_drowsiness_service", data.uid)
    return {"status": "start_drowsiness sent", "ros_response": str(response)}

@app.post("/end_drowsiness")
def end_drowsiness(data: UidModel):
    response = node.call_end_service()
    return {"status": "end_drowsiness sent", "ros_response": str(response)}

@app.post("/start_emotion")
def start_drowsiness(data: UidModel):
    response = node.call_uid_service("start_emotion_service", data.uid)
    return {"status": "start_emotion sent", "ros_response": str(response)}

