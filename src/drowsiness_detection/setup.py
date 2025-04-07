from setuptools import setup, find_packages
import os

package_name = 'drowsiness_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(), 
    data_files=[
        ('share/ament_index/resource_index/packages', 
         ['resource/' + package_name]), 

        ('share/' + package_name, ['package.xml']), 

        ('share/' + package_name + '/launch', 
         ['launch/drowsiness_detection_launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kimminee',
    maintainer_email='kimminee0312@konkuk.ac.kr',
    description='Drowsiness detection package for ROS 2',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            # 'usb_cam = drowsiness_detection.usb_camera_node:main',
            'face_detection_node = drowsiness_detection.face_detection_node:main',
            'drowsiness_detection_node = drowsiness_detection.drowsiness_detection_node:main', 
            'drowsiness_app_bridge_node = drowsiness_detection.drowsiness_app_bridge_node:main',
            'alert_node = drowsiness_detection.alert_node:main',
        ],
    },
)
