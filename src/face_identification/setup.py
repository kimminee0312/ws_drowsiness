from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'face_identification'

setup(
    name=package_name,
    version='0.1.0',   # package.xml 버전과 동일하게
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),         # resource/face_identification 파일이 있는지 확인
        ('share/' + package_name, ['package.xml']),  # package.xml 경로가 올바른지
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=[
        'setuptools',
        'opencv-python',
        'mediapipe',
        'keras-facenet',
        'firebase-admin',
    ],
    zip_safe=True,
    maintainer='kml',
    maintainer_email='kimminee0312@konkuk.ac.kr',
    description='Face identification nodes for the drowsiness system',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'face_register_node = face_identification.face_register_node:main',
            'face_identifier_node = face_identification.face_identifier_node:main',
            'face_emotion_node = face_identification.face_emotion_node:main',
            'emotion_status_uploader_node = face_identification.emotion_status_uploader_node:main',
            'emotion_session_uploader_node = face_identification.emotion_session_uploader_node:main',
        ],
    },
)
