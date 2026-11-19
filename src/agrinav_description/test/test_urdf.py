"""Generate the URDF with xacro and check it against the frame design.

Runs without ROS: it needs only the `xacro` Python module and, for the
`check_urdf` test, the `check_urdf` binary from liburdfdom-tools.
"""

from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
import pytest
import xacro

XACRO_FILE = Path(__file__).resolve().parents[1] / "urdf" / "agrinav.urdf.xacro"

# REP-105 chain plus the sensor frames from docs/architecture.md (child: parent).
EXPECTED_PARENTS = {
    "base_link": "base_footprint",
    "lidar_link": "base_link",
    "camera_link": "base_link",
    "camera_optical_frame": "camera_link",
    "imu_link": "base_link",
    "front_left_wheel_link": "base_link",
    "rear_left_wheel_link": "base_link",
    "front_right_wheel_link": "base_link",
    "rear_right_wheel_link": "base_link",
}


@pytest.fixture(scope="module")
def urdf_xml() -> str:
    return xacro.process_file(str(XACRO_FILE)).toxml()


@pytest.fixture(scope="module")
def robot(urdf_xml: str) -> ET.Element:
    return ET.fromstring(urdf_xml)


def test_tree_matches_design(robot: ET.Element) -> None:
    parents = {
        j.find("child").get("link"): j.find("parent").get("link") for j in robot.findall("joint")
    }
    links = {link.get("name") for link in robot.findall("link")}
    assert parents == EXPECTED_PARENTS
    assert links == set(EXPECTED_PARENTS) | {"base_footprint"}


def test_inertias_are_physical(robot: ET.Element) -> None:
    for link in robot.findall("link"):
        inertial = link.find("inertial")
        if inertial is None:
            continue
        name = link.get("name")
        assert float(inertial.find("mass").get("value")) > 0.0, name
        i = {k: float(v) for k, v in inertial.find("inertia").attrib.items()}
        tensor = np.array(
            [
                [i["ixx"], i["ixy"], i["ixz"]],
                [i["ixy"], i["iyy"], i["iyz"]],
                [i["ixz"], i["iyz"], i["izz"]],
            ]
        )
        principal = np.linalg.eigvalsh(tensor)
        assert np.all(principal > 0.0), name
        # Triangle inequality on principal moments: no rigid body violates it.
        a, b, c = principal
        assert a + b >= c and a + c >= b and b + c >= a, name


def test_wheel_joints_have_velocity_interfaces(robot: ET.Element) -> None:
    joints = robot.find("ros2_control").findall("joint")
    assert {j.get("name") for j in joints} == {
        "front_left_wheel_joint",
        "rear_left_wheel_joint",
        "front_right_wheel_joint",
        "rear_right_wheel_joint",
    }
    for joint in joints:
        commands = [c.get("name") for c in joint.findall("command_interface")]
        assert commands == ["velocity"]


def test_controller_plugin_only_with_parameters() -> None:
    without = xacro.process_file(str(XACRO_FILE)).toxml()
    with_file = xacro.process_file(
        str(XACRO_FILE), mappings={"controllers_file": "/tmp/controllers.yaml"}
    ).toxml()
    assert "GazeboSimROS2ControlPlugin" not in without
    assert "<parameters>/tmp/controllers.yaml</parameters>" in with_file


@pytest.mark.skipif(shutil.which("check_urdf") is None, reason="check_urdf not installed")
def test_check_urdf(urdf_xml: str, tmp_path: Path) -> None:
    urdf_path = tmp_path / "agrinav.urdf"
    urdf_path.write_text(urdf_xml)
    result = subprocess.run(
        ["check_urdf", str(urdf_path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "Successfully Parsed XML" in result.stdout
    assert "warn" not in (result.stdout + result.stderr).lower()
