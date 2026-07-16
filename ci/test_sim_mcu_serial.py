#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Functional test for tools/oomwoo_sim_mcu_serial.py.

This tool fakes the STM32 I/O board over a PTY so CPU-side bridge code can be
written before the board exists. Two defects previously shipped past a
py_compile-only check, and both were fatal to that job:

  * closing the PTY slave left no slave-side holder, so reads on the master
    returned EIO and the tool died;
  * a fresh PTY is in canonical mode with ECHO on, so the slave line discipline
    echoed each frame back and the tool acked its own heartbeats as commands.

py_compile cannot see either. This opens the link like a real client would and
asserts behaviour.
"""

import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE.parent / "ubuntu" / "tools" / "oomwoo_sim_mcu_serial.py"
LINK = "/tmp/oomwoo-mcu-serial-citest"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def frames(blob: str):
    out = []
    for line in blob.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            fail(f"emitted a non-JSON line: {line!r}")
    return out


def main() -> int:
    period = 0.2
    window = 1.5
    # With ECHO left on, the tool reads back its own frames, acks them, and that
    # ack echoes too -- it collapses into a self-feeding loop and STALLS. The
    # symptom is a stalled heartbeat stream, so assert the rate, not merely ">0".
    expect_min = 3

    log = open("/tmp/sim_mcu_citest.log", "w+")
    proc = subprocess.Popen(
        [sys.executable, str(TOOL), "--link", LINK, "--period", str(period)],
        stdout=log, stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(50):                       # wait for the link to appear
            if os.path.exists(LINK):
                break
            if proc.poll() is not None:
                fail("the tool exited before creating its link (EIO regression?)")
            time.sleep(0.1)
        else:
            fail(f"{LINK} never appeared")

        fd = os.open(LINK, os.O_RDWR | os.O_NOCTTY)

        # --- collect telemetry WITHOUT sending anything ----------------------
        time.sleep(window)
        got = frames(os.read(fd, 65536).decode(errors="replace"))
        beats = [f for f in got if f.get("type") == "heartbeat"]
        acks = [f for f in got if f.get("type") == "ack"]

        if not beats:
            fail("no heartbeat frames were emitted at all")
        # The real echo-regression symptom: the stream stalls after ~1 frame.
        if len(beats) < expect_min:
            fail(f"heartbeat stream stalled: {len(beats)} frame(s) in {window}s at "
                 f"period={period}s (expected >={expect_min}). The tool is most "
                 f"likely acking its own echoed frames -- PTY needs raw mode.")
        # A stalled tool never advances its sequence counter either.
        if beats[-1].get("seq", 0) < expect_min - 1:
            fail(f"heartbeat seq did not advance (last seq={beats[-1].get('seq')}); "
                 f"the emit loop is stuck")
        if acks:
            fail(f"tool acked itself {len(acks)}x without any command sent "
                 f"(PTY echo regression -- needs raw mode)")
        print(f"ok  heartbeat stream healthy: {len(beats)} frames in {window}s, "
              f"seq advanced to {beats[-1].get('seq')}")
        print("ok  phantom acks: 0 (raw mode holding)")

        for key in ("battery_mv", "bumper", "cliff", "wheel_drop", "estop"):
            if key not in beats[0]:
                fail(f"heartbeat is missing the '{key}' field")
        print("ok  heartbeat carries the MCU safety fields")

        # --- a real command must still be acked ------------------------------
        os.write(fd, b"PING\n")
        time.sleep(0.8)
        replies = [f for f in frames(os.read(fd, 65536).decode(errors="replace"))
                   if f.get("type") == "ack"]
        if not replies:
            fail("a real command was not acked")
        print(f"ok  real command acked: {json.dumps(replies[0])[:70]}")

        os.close(fd)

        if proc.poll() is not None:
            fail("the tool died during the session")
        print("ok  survived the session (no EIO)")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.seek(0)
        body = log.read()
        for bad in ("Traceback", "EIO", "Errno 5"):
            if bad in body:
                fail(f"tool log contains {bad!r}:\n{body}")

    print("PASS: oomwoo_sim_mcu_serial")
    return 0


if __name__ == "__main__":
    sys.exit(main())
