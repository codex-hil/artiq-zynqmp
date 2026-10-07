#!/usr/bin/env python3
"""Capture the A53 diagnostic after starting it on an explicitly supplied UART."""
import argparse
import json
from pathlib import Path
import time

import serial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--ocm", action="store_true", help="Expect DDR NOT_RUN for OCM diagnostic")
    options = parser.parse_args()
    tests = {name: "NOT_RUN" for name in ["uart", "uart_rx", "ddr", "timer", "interrupts"]}
    lines = []
    deadline = time.monotonic() + options.timeout
    with serial.Serial(options.port, 115200, timeout=0.25, write_timeout=1) as uart:
        while time.monotonic() < deadline:
            line = uart.readline().decode("ascii", errors="replace").strip()
            if not line:
                continue
            print(line, flush=True)
            lines.append(line)
            if line == "UART ECHO READY":
                uart.write(b"PING")
                uart.flush()
            fields = line.split()
            if len(fields) >= 3 and fields[0] == "TEST" and fields[1] in tests:
                tests[fields[1]] = fields[2]
            if line.startswith("BRINGUP COMPLETE"):
                break
    if "PONG" not in lines and tests["uart_rx"] == "PASS":
        tests["uart_rx"] = "FAIL"
    result = {"kind": "hardware", "port": options.port, "baud": 115200,
              "time": time.time(), "tests": tests, "uart_log": lines}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(result, indent=2) + "\n")
    return 0 if all(status == ("NOT_RUN" if options.ocm and name == "ddr" else "PASS")
                    for name, status in tests.items()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
