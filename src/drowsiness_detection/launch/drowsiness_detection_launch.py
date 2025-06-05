from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Node(
        #     package='drowsiness_detection',
        #     executable='usb_camera_node',
        #     name='usb_camera_node',
        #     output='screen'
        # ),
        Node(
            package='drowsiness_detection',
            executable='face_detection_node',
            name='face_detection_node',
            output='screen'
        ),
        Node(
            package='drowsiness_detection',
            executable='yawn_detection_node',
            name='yawn_detection_node',
            output='screen'
        ),
        Node(
            package='drowsiness_detection',
            executable='eye_detection_node',
            name='eye_detection_node',
            output='screen'
        ),
        Node(
            package='drowsiness_detection',
            executable='drowsiness_detection_node',
            name='drowsiness_detection_node',
            output='screen'
        ),
        Node(
            package='drowsiness_detection',
            executable='status_uploader_node',
            name='status_uploader_node',
            output='screen'
        ),
        Node(
            package='drowsiness_detection',
            executable='drowsy_session_uploader_node',
            name='drowsy_session_uploader_node',
            output='screen'
        ),
        Node(
            package='drowsiness_detection',
            executable='alert_node',
            name='alert_node',
            output='screen' 
        )
    ])
