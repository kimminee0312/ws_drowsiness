import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import mediapipe as mp
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms
import torch.nn as nn
import os

EMOTION_LABELS = {
    0: "positive",
    1: "neutral",
    2: "negative"
}

class DeepCNN(nn.Module):
    def __init__(self, num_classes=3):
        super(DeepCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout(0.25),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout(0.25),
            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout(0.25)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 6 * 6, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)

class EmotionPublishNode(Node):
    def __init__(self):
        super().__init__('face_emotion_node')
        self.publisher_ = self.create_publisher(String, '/emotion/status', 10)
        self.bridge = CvBridge()
        self.latest_frame = None  # 🟡 최신 프레임 저장용

        self.current_uid = None
        self.active = False

        self.create_subscription(String, '/current_uid', self.uid_callback, 10)
        self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = DeepCNN()
        model_path = "/home/kml/workspace/ws_drowsiness/src/face_identification/model/korean_emotion_model_3class_finetuned_final.pth"
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model = self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((48, 48)),
            transforms.ToTensor(),
            transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
        ])

        self.face_detection = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)

        # 🟢 감정 추론 주기를 0.33초 (약 3FPS)로 제한
        self.timer = self.create_timer(0.33, self.timer_callback)

        self.get_logger().info("🔐 감정 인식 노드 실행 중...")

    def uid_callback(self, msg):
        raw = msg.data.strip()
        if not raw.startswith("[emotion]"):
            self.get_logger().info("⚠️ [emotion] prefix 없음 → 감정 인식 비활성화")
            self.active = False
            self.current_uid = None
            return

        self.current_uid = raw.replace("[emotion]", "").strip()
        self.active = True
        self.get_logger().info(f"✅ 감정 인식 시작 - 사용자 UID: {self.current_uid}")

    def image_callback(self, img_msg: Image):
        if not self.active:
            return
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(img_msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f"CVBridge 변환 실패: {e}")

    def timer_callback(self):
        if not self.active or self.latest_frame is None:
            return

        frame = self.latest_frame.copy()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.face_detection.process(frame_rgb)

        output_frame = frame.copy()

        if result.detections:
            for detection in result.detections:
                h, w, _ = frame.shape
                bbox = detection.location_data.relative_bounding_box
                x_min = int(bbox.xmin * w)
                y_min = int(bbox.ymin * h)
                box_width = int(bbox.width * w)
                box_height = int(bbox.height * h)

                x_min = max(0, x_min)
                y_min = max(0, y_min)
                x_max = min(w, x_min + box_width)
                y_max = min(h, y_min + box_height)

                face_img = frame[y_min:y_max, x_min:x_max]
                if face_img.size == 0:
                    continue

                input_tensor = self.transform(face_img).unsqueeze(0).to(self.device)

                with torch.no_grad():
                    output = self.model(input_tensor)
                    probs = F.softmax(output, dim=1)
                    pred = torch.argmax(probs, dim=1).item()
                    emotion = EMOTION_LABELS[pred]
                    confidence = probs[0][pred].item()

                msg = String()
                msg.data = emotion
                self.publisher_.publish(msg)

                cv2.rectangle(output_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                label_text = f"{emotion} ({confidence*100:.1f}%)"
                cv2.putText(output_frame, label_text, (x_min, y_min - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                break

        cv2.imshow("Emotion Recognition (3-Class)", output_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            rclpy.shutdown()

    def destroy_node(self):
        super().destroy_node()
        self.face_detection.close()
        cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = EmotionPublishNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()