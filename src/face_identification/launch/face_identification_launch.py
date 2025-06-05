from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='face_identification',
            executable='face_register_node',
            name='face_register_node',
            output='screen'
        ),
        Node(
            package='face_identification',
            executable='face_identifier_node',
            name='face_identifier_node',
            output='screen'
        ),
        Node(
            package='face_identification',
            executable='face_emotion_node',
            name='face_emotion_node',
            output='screen'
        ),
        Node(
            package='face_identification',
            executable='emotion_status_uploader_node',
            name='emotion_status_uploader_node',
            output='screen'
        ),
        Node(
            package='face_identification',
            executable='emotion_session_uploader_node',
            name='emotion_session_uploader_node',
            output='screen'
        )
    ])
