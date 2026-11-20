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

The workspace builds and its tests pass in the Jazzy container. In a headless
run of `orchard_small`, `/odometry/filtered` and `/scan` are published,
`tf2_monitor odom base_footprint` lists a single broadcaster, and on a closed
30 m drive the EKF's final pose error against `/ground_truth/odom` is well below
that of wheel odometry alone. The measured values and the commands that produced
them are in the localization pull request.

The skid-steer `wheel_separation_multiplier` in `config/controllers.yaml` was
calibrated against `/ground_truth/odom` by commanding an in-place turn and
comparing the commanded and true yaw change; the comment next to it records the
measurement.

To repeat the topic checks, start `docker compose up --build sim` and from
another terminal run, one at a time:

```bash
docker compose exec sim /entrypoint.sh ros2 topic hz /odometry/filtered
docker compose exec sim /entrypoint.sh ros2 topic echo /scan --once
docker compose exec sim /entrypoint.sh ros2 run tf2_ros tf2_monitor odom base_footprint
```

Rates are reported in wall-clock time: without a GPU the simulation runs below
real time and every rate drops by the same factor.
