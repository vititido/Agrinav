"""Online asynchronous SLAM with slam_toolbox; publishes /map and map -> odom.

ros2 launch agrinav_bringup slam.launch.py
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    # The upstream launch file drives the node's lifecycle transitions.
    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PathJoinSubstitution(
                    [FindPackageShare("slam_toolbox"), "launch", "online_async_launch.py"]
                ),
                launch_arguments={
                    "use_sim_time": "true",
                    "slam_params_file": PathJoinSubstitution(
                        [FindPackageShare("agrinav_bringup"), "config", "slam_toolbox.yaml"]
                    ),
                }.items(),
            )
        ]
    )
