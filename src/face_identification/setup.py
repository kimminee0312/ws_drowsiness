from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'face_identification'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kml',
    maintainer_email='kimminee0312@konkuk.ac.kr',
    description='TODO: Package description',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'face_register_node = face_identification.face_register_node:main',
            'face_identifier_node = face_identification.face_identifier_node:main',
            'face_emotion_node = face_identification.face_emotion_node:main',
        ],
    },
)
