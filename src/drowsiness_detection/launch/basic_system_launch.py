from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='drowsiness_detection',
            executable='usb_camera_node',
            name='usb_camera_node',
            output='screen'
        ),
        Node(
            package='drowsiness_detection',
            executable='multi_uid_service_server_node',
            name='multi_uid_service_server_node',
            output='screen'
        ),
    ])
