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
