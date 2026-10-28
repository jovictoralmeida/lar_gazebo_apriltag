#!/bin/bash
# Prepara o ambiente ROS. Tambem e "sourced" pelo .bashrc (argumento "true").
source /opt/ros/noetic/setup.bash
[ -f /ws/devel/setup.bash ] && source /ws/devel/setup.bash

LAR="$(rospack find lar_gazebo 2>/dev/null || true)"
# Acessorios padrao do Husky (laser LMS1XX + Realsense + ground truth), como no README
[ -n "$LAR" ] && [ -f "$LAR/husky_accessories.sh" ] && source "$LAR/husky_accessories.sh"
[ -n "$LAR" ] && export GAZEBO_MODEL_PATH="${GAZEBO_MODEL_PATH:+$GAZEBO_MODEL_PATH:}$LAR/models"

# A AprilTag e anexada ao Husky via CPR_URDF_EXTRAS
# (HUSKY_URDF_EXTRAS ja e usado pelo lar_gazebo para o gazebo_ground_truth).
export CPR_URDF_EXTRAS="$(rospack find lar_apriltag)/urdf/apriltag_mount.urdf.xacro"

if [ "$1" = "true" ] && [ "$#" -eq 1 ]; then return 0 2>/dev/null || exit 0; fi
exec "$@"
