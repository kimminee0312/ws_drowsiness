from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    basic_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('drowsiness_detection'), 'launch', 'basic_system_launch.py')
        )
    )
    
    face_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('face_identification'), 'launch', 'face_identification_launch.py')
        )
    )

    drowsy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('drowsiness_detection'), 'launch', 'drowsiness_detection_launch.py')
        )
    )

    return LaunchDescription([
        basic_launch,
        face_launch,
        drowsy_launch
    ])
