"""Gazebo orchard with the agrinav robot, the ros_gz bridge and its controllers.

ros2 launch agrinav_bringup sim.launch.py world:=orchard_small headless:=false rviz:=true
"""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
import yaml

from agrinav_gazebo.generate_orchard import load_params
from agrinav_gazebo.orchard import generate, to_sdf

# The installed share directory may be read-only, so generated worlds live here.
WORLD_CACHE = Path.home() / ".ros" / "agrinav" / "worlds"


def world_file(world: str) -> Path:
    """Return the SDF for `world`, writing it if it is missing or out of date."""
    gazebo_share = Path(get_package_share_directory("agrinav_gazebo"))
    sdf = to_sdf(generate(load_params(gazebo_share / "config" / "worlds.yaml", world)))
    path = WORLD_CACHE / f"{world}.sdf"
    if not path.exists() or path.read_text() != sdf:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sdf)
    return path


def launch_world(context: LaunchContext) -> list:
    world = LaunchConfiguration("world").perform(context)
    headless = LaunchConfiguration("headless").perform(context).lower() == "true"
    gazebo_share = Path(get_package_share_directory("agrinav_gazebo"))

    spawn = yaml.safe_load((gazebo_share / "worlds" / world / "ground_truth.yaml").read_text())[
        "spawn"
    ]
    # -r starts the clock; -s skips the GUI; headless rendering lets the
    # gpu_lidar and camera render through EGL without a display.
    gz_args = (
        f"-r -s --headless-rendering {world_file(world)}"
        if headless
        else (f"-r {world_file(world)}")
    )

    gazebo = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]),
        launch_arguments={"gz_args": gz_args, "on_exit_shutdown": "true"}.items(),
    )
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "agrinav",
            "-x",
            str(spawn["x"]),
            "-y",
            str(spawn["y"]),
            "-z",
            "0.05",
            "-Y",
            str(spawn["yaw"]),
        ],
        output="screen",
    )
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        parameters=[{"use_sim_time": True}],
    )
    diff_drive = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"],
        parameters=[{"use_sim_time": True}],
    )
    return [
        gazebo,
        spawn_robot,
        # Controllers start in order once the robot exists: the broadcaster
        # first, then the drive controller.
        RegisterEventHandler(
            OnProcessExit(target_action=spawn_robot, on_exit=[joint_state_broadcaster])
        ),
        RegisterEventHandler(
            OnProcessExit(target_action=joint_state_broadcaster, on_exit=[diff_drive])
        ),
    ]


def generate_launch_description() -> LaunchDescription:
    bringup = FindPackageShare("agrinav_bringup")
    controllers = PathJoinSubstitution([bringup, "config", "controllers.yaml"])
    xacro_file = PathJoinSubstitution(
        [FindPackageShare("agrinav_description"), "urdf", "agrinav.urdf.xacro"]
    )
    robot_description = ParameterValue(
        Command(["xacro ", xacro_file, " controllers_file:=", controllers]), value_type=str
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("world", default_value="orchard_small"),
            DeclareLaunchArgument("headless", default_value="false"),
            DeclareLaunchArgument("rviz", default_value="true"),
            AppendEnvironmentVariable(
                "GZ_SIM_RESOURCE_PATH",
                PathJoinSubstitution([FindPackageShare("agrinav_gazebo"), "models"]),
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[{"robot_description": robot_description, "use_sim_time": True}],
            ),
            OpaqueFunction(function=launch_world),
            IncludeLaunchDescription(
                PathJoinSubstitution([bringup, "launch", "localization.launch.py"])
            ),
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                parameters=[
                    {
                        "config_file": PathJoinSubstitution([bringup, "config", "gz_bridge.yaml"]),
                        "use_sim_time": True,
                    }
                ],
                output="screen",
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                arguments=["-d", PathJoinSubstitution([bringup, "rviz", "sim.rviz"])],
                parameters=[{"use_sim_time": True}],
                condition=IfCondition(LaunchConfiguration("rviz")),
            ),
        ]
    )
