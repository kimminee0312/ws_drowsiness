cmake_minimum_required(VERSION 3.8)
project(srv_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)

# ✅ 여기가 중요: Python 바인딩을 생성하려면 해당 옵션 추가
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/Uid.srv"
  DEPENDENCIES builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
