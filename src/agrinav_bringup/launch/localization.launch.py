"""Fuse wheel odometry and IMU, and project the lidar cloud for 2D mapping."""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    config = [FindPackageShare("agrinav_bringup"), "config"]
    return LaunchDescription(
        [
            Node(
                package="agrinav_bringup",
                executable="imu_covariance",
                parameters=[PathJoinSubstitution([*config, "imu_covariance.yaml"])],
                output="screen",
            ),
            Node(
                package="robot_localization",
                executable="ekf_node",
                name="ekf_filter_node",
                parameters=[PathJoinSubstitution([*config, "ekf.yaml"])],
                output="screen",
            ),
            Node(
                package="pointcloud_to_laserscan",
                executable="pointcloud_to_laserscan_node",
                name="pointcloud_to_laserscan",
                parameters=[PathJoinSubstitution([*config, "pointcloud_to_laserscan.yaml"])],
                remappings=[("cloud_in", "/points"), ("scan", "/scan")],
                output="screen",
            ),
        ]
    )
