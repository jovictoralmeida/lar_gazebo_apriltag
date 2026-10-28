#!/bin/bash
# Uso: ./scripts/sim.sh [args do launch, ex.: cam_z:=3.0 hector_slam:=true]
cd "$(dirname "$0")/.."
xhost +local:docker >/dev/null 2>&1 || true
docker compose run --rm lar_apriltag roslaunch lar_apriltag lar_husky_apriltag.launch "$@"
