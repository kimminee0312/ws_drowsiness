from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='face_identification',
            executable='face_register_node',
            name='face_register_node',
            output='screen'
        )
    ])
