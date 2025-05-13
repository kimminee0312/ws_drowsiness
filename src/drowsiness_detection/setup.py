from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'drowsiness_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(), 
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]), 

        ('share/' + package_name, ['package.xml']), 

        ('share/' + package_name + '/launch', ['launch/drowsiness_detection_launch.py']),

        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),


    ],
    install_requires=[''
    'plotly>=5.0.0',
    ],
    maintainer='kimminee',
    maintainer_email='kimminee0312@konkuk.ac.kr',
    description='Drowsiness detection package for ROS 2',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'test_email_publisher = drowsiness_detection.test_email_publisher:main',
            'multi_uid_service_server_node = drowsiness_detection.multi_uid_service_server_node:main',
            'usb_camera_node = drowsiness_detection.usb_camera_node:main',
            'face_detection_node = drowsiness_detection.face_detection_node:main',
            'yawn_detection_node = drowsiness_detection.yawn_detection_node:main',
            'drowsiness_detection_node = drowsiness_detection.drowsiness_detection_node:main', 
            'alert_node = drowsiness_detection.alert_node:main',
            'status_upload_node = drowsiness_detection.status_upload_node:main',
        ],
    },
    zip_safe=False,
)
