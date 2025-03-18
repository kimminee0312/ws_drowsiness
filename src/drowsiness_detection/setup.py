from setuptools import setup, find_packages

package_name = 'drowsiness_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(), 
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),  # 📌 패키지 인덱스 등록
        ('share/' + package_name, ['package.xml']),  # 📌 package.xml 추가
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description='Drowsiness detection package for ROS 2',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'drowsiness_detector = drowsiness_detection.drowsiness_detection_node:main',  # 📌 실행 경로 확인
        ],
    },
)
