cmake_minimum_required(VERSION 3.0.2)
project(lar_apriltag)
find_package(catkin REQUIRED COMPONENTS message_generation std_msgs)
add_message_files(FILES RobotPoseError.msg)
generate_messages(DEPENDENCIES std_msgs)
catkin_package(CATKIN_DEPENDS message_runtime std_msgs)
catkin_install_python(PROGRAMS scripts/apriltag_robot_localization.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(DIRECTORY launch config urdf sdf media rviz
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
