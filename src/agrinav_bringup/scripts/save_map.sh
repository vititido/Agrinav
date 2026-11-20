#!/bin/bash
# Save the occupancy grid and the slam_toolbox pose graph under one prefix.
#   ros2 run agrinav_bringup save_map.sh <output_prefix>
# Writes <prefix>.pgm/.yaml (map_server format) and <prefix>.posegraph/.data
# (slam_toolbox serialized graph, reloadable to continue mapping).
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: save_map.sh <output_prefix>" >&2
  exit 2
fi
prefix=$(realpath -m "$1")
mkdir -p "$(dirname "$prefix")"

ros2 run nav2_map_server map_saver_cli -f "$prefix" --ros-args -p use_sim_time:=true
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph \
  "{filename: '$prefix'}"
