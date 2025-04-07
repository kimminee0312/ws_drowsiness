import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import firebase_admin
from firebase_admin import credentials, firestore

class FirebaseBridgeNode(Node):
    def __init__(self):
        super().__init__('firebase_bridge_node')
        self.subscriber = self.create_subscription(String, '/drowsiness/status', self.callback, 10)

        cred = credentials.Certificate('/path/to/firebase-key.json')
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def callback(self, msg):
        state = msg.data
        doc_ref = self.db.collection('users').document('test_user')
        doc_ref.set({'state': state})
        self.get_logger().info(f'Uploaded status: {state}')

def main(args=None):
    rclpy.init(args=args)
    node = FirebaseBridgeNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
