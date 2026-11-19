"""Fill missing Gazebo IMU covariances from the configured sensor noise."""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu


class ImuCovariance(Node):
    def __init__(self) -> None:
        super().__init__("imu_covariance")
        self.angular_variance = self.declare_parameter("angular_velocity_variance", 0.0).value
        self.linear_variance = self.declare_parameter("linear_acceleration_variance", 0.0).value
        if self.angular_variance <= 0.0 or self.linear_variance <= 0.0:
            raise ValueError("IMU variances must be positive; load imu_covariance.yaml")
        self.publisher = self.create_publisher(Imu, "/imu/data", qos_profile_sensor_data)
        self.subscription = self.create_subscription(
            Imu, "/imu/data_raw", self.publish_with_covariance, qos_profile_sensor_data
        )

    def publish_with_covariance(self, message: Imu) -> None:
        # Zero means unknown in sensor_msgs/Imu. Preserve supplied covariances,
        # including the -1 sentinel for an unavailable measurement.
        for field, variance in (
            ("angular_velocity_covariance", self.angular_variance),
            ("linear_acceleration_covariance", self.linear_variance),
        ):
            if not any(getattr(message, field)):
                setattr(
                    message, field, [variance, 0.0, 0.0, 0.0, variance, 0.0, 0.0, 0.0, variance]
                )
        self.publisher.publish(message)


def main() -> None:
    rclpy.init()
    node = ImuCovariance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
