#!/usr/bin/env python3
"""Simulate the OOMWOO CPU-to-MCU serial link with a pseudo-terminal.

The real consumer vacuum profile should talk to an MCU over a custom serial
protocol. This helper creates a PTY symlink so ROS2 bridge code can open a
serial-like device before the real STM32 firmware exists.
"""

from __future__ import annotations

import argparse
import json
import os
import pty
import select
import signal
import sys
import time
import tty
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--link",
        default="/tmp/oomwoo-mcu-serial",
        help="Symlink path for the simulated serial device.",
    )
    parser.add_argument(
        "--period",
        type=float,
        default=1.0,
        help="Seconds between heartbeat/sensor frames.",
    )
    parser.add_argument(
        "--battery-mv",
        type=int,
        default=14800,
        help="Battery voltage reported in heartbeat frames.",
    )
    return parser.parse_args()


def write_frame(master_fd: int, frame: dict[str, object]) -> None:
    payload = json.dumps(frame, separators=(",", ":")) + "\n"
    os.write(master_fd, payload.encode("utf-8"))


def install_link(slave_name: str, link: Path) -> None:
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(slave_name)


def parse_command(line: str) -> dict[str, object]:
    line = line.strip()
    if not line:
        return {"type": "empty"}
    try:
        value = json.loads(line)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    return {"cmd": line}


def main() -> int:
    args = parse_args()
    link = Path(args.link)
    master_fd, slave_fd = pty.openpty()
    # Raw mode: a fresh PTY starts in canonical mode with ECHO on, so the slave
    # line discipline echoes every frame we write back to the master. We then
    # read our own heartbeats and ack them as phantom commands.
    tty.setraw(slave_fd)
    slave_name = os.ttyname(slave_fd)
    # Keep the slave open for the lifetime of the process. Closing it leaves the
    # PTY with no slave-side holder, and reads on the master then fail with EIO
    # as soon as a client disconnects (or immediately, if none ever attaches).
    install_link(slave_name, link)

    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    print(f"OOMWOO simulated MCU serial link: {link} -> {slave_name}", flush=True)
    print("Open the link from ROS2 bridge code as a serial device.", flush=True)

    seq = 0
    pending = b""
    next_frame = 0.0

    try:
        while running:
            now = time.monotonic()
            timeout = max(0.0, min(args.period, next_frame - now))
            readable, _, _ = select.select([master_fd], [], [], timeout)

            if master_fd in readable:
                chunk = os.read(master_fd, 4096)
                if chunk:
                    pending += chunk
                    while b"\n" in pending:
                        raw, pending = pending.split(b"\n", 1)
                        command = parse_command(raw.decode("utf-8", errors="replace"))
                        write_frame(
                            master_fd,
                            {
                                "type": "ack",
                                "seq": seq,
                                "received": command,
                            },
                        )

            now = time.monotonic()
            if now >= next_frame:
                frame = {
                    "type": "heartbeat",
                    "seq": seq,
                    "battery_mv": args.battery_mv,
                    "bumper": False,
                    "cliff": False,
                    "wheel_drop": False,
                    "estop": False,
                    "motors_enabled": True,
                }
                write_frame(master_fd, frame)
                seq += 1
                next_frame = now + args.period
    finally:
        if link.exists() or link.is_symlink():
            link.unlink()
        os.close(master_fd)
        os.close(slave_fd)

    return 0


if __name__ == "__main__":
    sys.exit(main())
