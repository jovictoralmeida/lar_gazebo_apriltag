#!/bin/bash
cd "$(dirname "$0")/.."
xhost +local:docker >/dev/null 2>&1 || true
docker compose run --rm lar_apriltag bash -i
