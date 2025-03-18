import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge

class UsbCameraNode(Node):
    def __init__(self):
        super().__init__('usb_camera_node')
        self.publisher = self.create_publisher(Image, '/camera/image_raw', 10)
        self.bridge = CvBridge()
        self.cap = cv2.VideoCapture(0)
        self.timer = self.create_timer(0.03, self.publish_frame)
        self.get_logger().info("USB Camera Node Started ✅")

        if not self.cap.isOpened():
            self.get_logger().error("-------------Unable to open USB camera-------------")
            raise RuntimeError("Failed to open USB camera")
    
    def publish_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn("⚠️ Failed to capture frame from USB camera")
            return

        cv2.imshow("USB Camera Feed", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # 'q'를 누르면 종료
            self.get_logger().info("Shutting down USB Camera Node ❌")
            self.destroy_node()
            rclpy.shutdown()

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

def main(args=None):
    rclpy.init()
    node = UsbCameraNode()
    rclpy.spin(node)
    node.release()

if __name__ == "__main__":
    main()
