"""Use WASD controls with the existing ROS keyboard teleoperation node."""

import teleop_twist_keyboard as teleop


def main() -> None:
    teleop.moveBindings = {
        "w": (1, 0, 0, 0),
        "s": (-1, 0, 0, 0),
        "a": (0, 0, 0, 1),
        "d": (0, 0, 0, -1),
        "r": (0, 0, 0, 0),
    }
    # The upstream linear-speed shortcut uses w, which now means forward.
    teleop.speedBindings = {}
    teleop.msg = """
Drive the robot with the terminal focused:
    w : forward
    s : backward
    a : turn left
    d : turn right
    r : stop

Any other key also stops the robot. CTRL-C to quit.
"""
    teleop.main()
