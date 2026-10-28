#!/bin/bash
cd "$(dirname "$0")/.."
docker compose run --rm lar_apriltag rosrun teleop_twist_keyboard teleop_twist_keyboard.py cmd_vel:=/husky_velocity_controller/cmd_vel
