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

Drive the robot from a second terminal (keys `i`, `j`, `l`, `,`). Commands run
through `/entrypoint.sh`, which loads the ROS environment:

```bash
docker compose exec sim /entrypoint.sh ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p stamped:=true -r cmd_vel:=/diff_drive_controller/cmd_vel
```
