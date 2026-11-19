"""Exercise the installed keyboard executable with a terminal and ROS subscriber."""

import os
import pty
import select
import signal
import subprocess
import termios
import time

from geometry_msgs.msg import TwistStamped
import rclpy


def test_wasd_publishes_stamped_commands() -> None:
    rclpy.init()
    node = rclpy.create_node("test_wasd")
    received = []
    subscription = node.create_subscription(
        TwistStamped, "/test_wasd/cmd_vel", received.append, 10
    )
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [
            "ros2",
            "run",
            "agrinav_bringup",
            "teleop",
            "--ros-args",
            "-p",
            "stamped:=true",
            "-r",
            "cmd_vel:=/test_wasd/cmd_vel",
        ],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        start_new_session=True,
    )
    os.close(slave)
    try:
        output = b""
        deadline = time.monotonic() + 15
        while b"CTRL-C to quit" not in output and time.monotonic() < deadline:
            assert process.poll() is None, output.decode(errors="replace")
            if select.select([master], [], [], 0.1)[0]:
                output += os.read(master, 4096)
        assert b"CTRL-C to quit" in output, output.decode(errors="replace")
        deadline = time.monotonic() + 10
        while node.count_publishers("/test_wasd/cmd_vel") == 0:
            assert time.monotonic() < deadline, "keyboard publisher was not discovered"
            rclpy.spin_once(node, timeout_sec=0.1)

        # Graph discovery can precede DDS matching. Establish delivery with stop
        # commands before testing a single movement keypress.
        deadline = time.monotonic() + 5
        while not received and time.monotonic() < deadline:
            os.write(master, b"r")
            rclpy.spin_once(node, timeout_sec=0.1)
        assert received, "DDS did not deliver the initial stop"
        rclpy.spin_once(node, timeout_sec=0.1)

        for key, expected in [
            ("w", (0.5, 0.0)),
            ("r", (0.0, 0.0)),
            ("s", (-0.5, 0.0)),
            ("a", (0.0, 1.0)),
            ("d", (0.0, -1.0)),
            ("?", (0.0, 0.0)),
        ]:
            # tty.setraw flushes pending input, so wait until it is ready.
            deadline = time.monotonic() + 3
            while termios.tcgetattr(master)[3] & termios.ICANON:
                assert time.monotonic() < deadline, "keyboard did not enter raw mode"
                rclpy.spin_once(node, timeout_sec=0.01)
            received.clear()
            os.write(master, key.encode())
            deadline = time.monotonic() + 3
            while not received and time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=0.1)
            if not received and select.select([master], [], [], 0)[0]:
                output += os.read(master, 4096)
            assert received, f"no command for {key}: {output.decode(errors='replace')}"
            message = received[-1]
            assert (message.twist.linear.x, message.twist.angular.z) == expected
            assert message.header.stamp.sec > 0

        received.clear()
        os.write(master, b"\x03")
        deadline = time.monotonic() + 3
        while not received and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        assert received, "exit did not publish a stop"
        assert received[-1].twist.linear.x == received[-1].twist.angular.z == 0.0
        assert process.wait(timeout=10) == 0
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
        os.close(master)
        node.destroy_subscription(subscription)
        node.destroy_node()
        rclpy.shutdown()
