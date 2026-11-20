"""Verify IMU metadata on the ROS output without changing the measurements."""

import time

import pytest
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu

from agrinav_bringup.imu_covariance import ImuCovariance


@pytest.mark.parametrize("existing", [0.0, 0.1, -1.0])
def test_missing_covariance_is_filled_and_existing_is_preserved(existing: float) -> None:
    rclpy.init(
        args=[
            "--ros-args",
            "-p",
            "angular_velocity_variance:=0.000025",
            "-p",
            "linear_acceleration_variance:=0.0004",
        ]
    )
    node = ImuCovariance()
    received = []
    subscription = node.create_subscription(
        Imu, "/imu/data", received.append, qos_profile_sensor_data
    )
    message = Imu()
    message.header.frame_id = "imu_link"
    message.header.stamp.sec = 42
    message.angular_velocity.z = 0.3
    message.linear_acceleration.x = 0.2
    message.angular_velocity_covariance[0] = existing
    message.linear_acceleration_covariance[0] = existing
    try:
        deadline = time.monotonic() + 5
        while not received and time.monotonic() < deadline:
            node.publish_with_covariance(message)
            rclpy.spin_once(node, timeout_sec=0.1)
        assert received, "IMU output was not received"
        result = received[-1]
        assert result.header == message.header
        assert result.angular_velocity.z == 0.3
        assert result.linear_acceleration.x == 0.2
        assert list(result.orientation_covariance) == list(message.orientation_covariance)
        for field, expected in [
            ("angular_velocity_covariance", 0.000025),
            ("linear_acceleration_covariance", 0.0004),
        ]:
            covariance = getattr(result, field)
            if existing:
                assert covariance[0] == existing
                assert list(covariance[1:]) == [0.0] * 8
            else:
                assert [covariance[i] for i in (0, 4, 8)] == [expected] * 3
                assert [covariance[i] for i in (1, 2, 3, 5, 6, 7)] == [0.0] * 6
    finally:
        node.destroy_subscription(subscription)
        node.destroy_node()
        rclpy.shutdown()
