import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import mediapipe as mp
import numpy as np
from keras_facenet import FaceNet
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

class FaceRegisterNode(Node):
    def __init__(self):
        super().__init__('face_register_node')
        self.bridge = CvBridge()

        # 얼굴 인식 도구 준비
        self.detector = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.7)
        self.embedder = FaceNet()

        # Firebase 초기화
        cred_path = "/home/kml/workspace/ws_drowsiness/firebase-key.json"
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

        self.current_uid = None
        self.embedding_registered = False

        # ROS 토픽 구독
        self.create_subscription(String, '/current_uid', self.uid_callback, 10)
        self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)

        self.get_logger().info("📸 얼굴 등록 노드 실행 중...")

    def uid_callback(self, msg):
        full_uid = msg.data.strip()
        
        if not full_uid.startswith("[face_register]"):
            self.get_logger().info("⚠️ [face_register] prefix 없음 → 무시됨")
            return
        
        uid = full_uid.replace("[face_register]", "").strip()

        if uid != self.current_uid:
            self.current_uid = uid
            self.embedding_registered = False  # 새로운 이메일일 때만 초기화

        self.get_logger().info(f"📩 얼굴 등록용 이메일 수신됨: {self.current_uid}")

    def image_callback(self, msg):
        if not self.current_uid or self.embedding_registered:
            return

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if results.detections:
            for det in results.detections:
                h, w, _ = frame.shape
                bbox = det.location_data.relative_bounding_box
                x1, y1 = int(bbox.xmin * w), int(bbox.ymin * h)
                x2, y2 = x1 + int(bbox.width * w), y1 + int(bbox.height * h)
                face_img = frame[y1:y2, x1:x2]

                if face_img.size == 0:
                    continue

                emb = self.embedder.embeddings([face_img])[0].tolist()
                self.save_embedding_to_firebase(self.current_uid, emb)
                self.embedding_registered = True
                self.get_logger().info(f"✅ 얼굴 임베딩 저장 완료: {self.current_uid}")
                return

    def save_embedding_to_firebase(self, uid, embedding):
        ref = self.db.collection("users").document(uid)
        ref.set({"face_id_registered": True}, merge=True)
        ref.collection("face_embedding").document("vector").set({
            "embedding": embedding,
            "created_at": datetime.now().isoformat()
        })


def main(args=None):
    rclpy.init(args=args)
    node = FaceRegisterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()