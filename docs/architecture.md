# State estimation

The simulation uses ROS 2 Jazzy and Gazebo Harmonic. Every estimation node uses
simulation time from `/clock`.

`robot_localization` fuses wheel linear x and angular z velocity from
`/diff_drive_controller/odom` with angular z velocity and linear x acceleration
from `/imu/data`. Wheel pose is not fused because it is integrated from the same
encoders. Ground truth is reserved for evaluation and never feeds the filter.

The EKF publishes `/odometry/filtered` and is the only publisher of
`odom -> base_footprint`. The wheel controller has `enable_odom_tf: false`.
`robot_state_publisher` owns the transforms from `base_footprint` to the body,
wheels, and sensors. No `map` frame exists until SLAM or localization is added.

`pointcloud_to_laserscan` transforms `/points` to `base_footprint`, selects a
height band above the chassis, and publishes `/scan`. Heights and ranges are in
`config/pointcloud_to_laserscan.yaml`. The converter only subscribes to the cloud
when a scan consumer exists; subscribe to `/scan` before diagnosing missing data.

The filter inputs, state masks, and timeout are in `config/ekf.yaml`. Measurement
covariances come from the controller and the simulated IMU. The Gazebo bridge
publishes `/imu/data_raw`; `imu_covariance` supplies missing gyro and acceleration
covariances before publishing `/imu/data`. Its YAML variances are the squared
sensor noise standard deviations. Existing nonzero covariance arrays and the
unavailable-measurement sentinel are preserved. These are initial
settings, not a claim of measured localization accuracy. Validate drift against
`/ground_truth/odom` on the same trajectory before tuning them.

References: [robot_localization configuration](https://docs.ros.org/en/jazzy/p/robot_localization/doc/configuring_robot_localization.html)
and [pointcloud_to_laserscan](https://github.com/ros-perception/pointcloud_to_laserscan).

## Validation

The three workspace packages build with `colcon build --symlink-install` on the
ROS 2 Jazzy desktop image. The 25 pytest cases pass, including the installed WASD
executable with a pseudo-terminal and ROS subscriber, URDF parsing, orchard
properties, and IMU covariance publication.

Full simulation validation is pending: the cloud network returned HTTP 403 for
`packages.ros.org`, preventing installation of `robot_localization`,
`pointcloud_to_laserscan`, and the simulation controller dependencies. Compilation
of these Python launch files does not establish that those runtime nodes work.
No localization accuracy or topic-rate measurements are claimed.

On a machine with ROS package access, rebuild and start `docker compose up --build
sim`. From another terminal, run these checks separately:

```bash
docker compose exec sim /entrypoint.sh ros2 topic hz /odometry/filtered
docker compose exec sim /entrypoint.sh ros2 topic echo /scan --once
docker compose exec sim /entrypoint.sh ros2 run tf2_ros tf2_monitor odom base_footprint
```

Verify filtered odometry is near the configured 50 Hz in simulation time, that
scan ranges contain finite returns, and that only the EKF publishes
`odom -> base_footprint`. Record `/ground_truth/odom`,
`/diff_drive_controller/odom`, `/odometry/filtered`, `/imu/data`, `/tf`, and
`/tf_static` during a closed trajectory of about 30 m. Compare final planar pose
errors after aligning their initial poses; the wheel and filtered errors must
be measured on the same run. Drift improvement remains unverified until then.
