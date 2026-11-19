"""Show the robot model in RViz with sliders for the wheel joints."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    share = FindPackageShare("agrinav_description")
    xacro_file = PathJoinSubstitution([share, "urdf", "agrinav.urdf.xacro"])
    rviz_config = PathJoinSubstitution([share, "rviz", "display.rviz"])

    # ParameterValue keeps the URDF as a string instead of letting launch
    # try to parse it as YAML.
    robot_description = ParameterValue(Command(["xacro ", xacro_file]), value_type=str)

    return LaunchDescription(
        [
            DeclareLaunchArgument("rviz", default_value="true"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(package="joint_state_publisher_gui", executable="joint_state_publisher_gui"),
            Node(
                package="rviz2",
                executable="rviz2",
                arguments=["-d", rviz_config],
                condition=IfCondition(LaunchConfiguration("rviz")),
            ),
        ]
    )
