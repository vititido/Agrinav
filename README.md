# agrinav

A ROS 2 mobile robot that maps an orchard, labels what it sees and carries out missions given in plain English.

Work in progress.

## Quick start

Requirements: Docker with Compose v2, on Ubuntu 24.04 or on Windows 11 with WSL2 (WSLg).

```bash
git clone https://github.com/vititido/agrinav.git
cd agrinav
```

On Linux, allow local containers to open windows on your display (once per login; WSLg does not need it):

```bash
xhost +local:
```

Build the image and start Gazebo with the robot in the small orchard, plus RViz:

```bash
docker compose up sim
```

The first build takes several minutes. With an NVIDIA GPU and the NVIDIA Container Toolkit, use `docker compose --profile gpu up sim-gpu` instead.

Drive the robot from a second terminal: `w` forward, `s` backward, `a` turn left,
`d` turn right, and `r` stop. Keep that terminal focused. Commands run
through `/entrypoint.sh`, which loads the ROS environment:

```bash
docker compose exec sim /entrypoint.sh ros2 run agrinav_bringup teleop --ros-args -p stamped:=true -r cmd_vel:=/diff_drive_controller/cmd_vel
```

After updating the source, stop the old simulation with Ctrl-C and rebuild it:

```bash
docker compose up --build sim
```

Run the keyboard command in a second Ubuntu/WSL terminal in this same directory,
not in the Gazebo window. Its help must list WASD and `r`; the upstream
`teleop_twist_keyboard` executable still uses its original keys. If ROS reports
`No executable found`, check that your checkout includes the `teleop` entry point
and recreate the simulation with the rebuild command above.

## State estimation

The simulation also starts an EKF for wheel odometry and IMU fusion, and a
converter from the 3D lidar cloud to a 2D scan. Rebuild after updating the source:

```bash
docker compose up --build sim
```

From a second terminal in the repository, check the filtered odometry and scan:

```bash
docker compose exec sim /entrypoint.sh ros2 topic hz /odometry/filtered
docker compose exec sim /entrypoint.sh ros2 topic echo /scan --once
```

Run these commands separately (Ctrl-C stops the rate check). `/scan` is produced
only while a subscriber exists. The EKF owns `odom -> base_footprint`; ground truth
is used only for validation. See [state estimation](docs/architecture.md).
