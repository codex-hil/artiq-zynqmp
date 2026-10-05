#!/usr/bin/env python3
"""Run on the Genesys Linux PS after loading the local-rtio gateware.

Requires a physical jumper JB1 -> JB2. Results are hardware evidence only when
this script actually accesses /dev/mem on the identified board. It never loads
or configures an FPGA and must not be used with the original blinker bitstream.
"""
import argparse
import ctypes
import json
import mmap
import os
from pathlib import Path
import platform
import time


class CSR:
    def __init__(self, mapping):
        if mapping["csr_base"] != 0xA0000000 or mapping["csr_data_width"] != 32:
            raise ValueError("Unexpected CSR aperture or ABI")
        self.registers = mapping["registers"]
        self.fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.mem = mmap.mmap(self.fd, 0x10000, offset=0xA0000000)

    def close(self):
        self.mem.close()
        os.close(self.fd)

    def location(self, name):
        register = self.registers[name]
        offset = register["address"] - 0xA0000000
        words = register["words"]
        if offset < 0 or offset + words * 4 > 0x10000 or offset % 4:
            raise ValueError("Invalid CSR range: " + name)
        return offset, words

    def read(self, name):
        offset, words = self.location(name)
        value = 0
        for index in range(words):
            value = (value << 32) | ctypes.c_uint32.from_buffer(self.mem, offset + index * 4).value
        return value

    def write(self, name, value):
        offset, words = self.location(name)
        for index in range(words):
            shift = (words - index - 1) * 32
            ctypes.c_uint32.from_buffer(self.mem, offset + index * 4).value = (value >> shift) & 0xFFFFFFFF

    def counter(self):
        self.write("rtio_counter_update", 1)
        return self.read("rtio_counter")

    def event(self, channel, address, timestamp, value):
        self.write("rtio_target", (channel << 8) | address)
        self.write("rtio_now", timestamp)
        # Target clears the 512-bit output payload. Commit only its last word.
        offset, words = self.location("rtio_o_data")
        ctypes.c_uint32.from_buffer(self.mem, offset + (words - 1) * 4).value = value
        status = self.read("rtio_o_status")
        if status:
            raise RuntimeError("RTIO output status: " + hex(status))

    def input_event(self, timeout):
        self.write("rtio_target", 1 << 8)
        self.write("rtio_i_timeout", timeout)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            status = self.read("rtio_i_status")
            if not status & 4:
                if status:
                    raise RuntimeError("RTIO input status: " + hex(status))
                return self.read("rtio_i_timestamp"), self.read("rtio_i_data")
            time.sleep(0.001)
        raise TimeoutError("RTIO input completion timed out")


def run(mapping):
    result = {"kind": "hardware", "hostname": platform.node(), "time": time.time(),
              "tests": {name: {"status": "NOT_RUN"} for name in
                  ["uart", "ddr", "ethernet", "ps_pl", "clocks", "timer", "interrupts",
                   "rtio_counter", "ttl_output", "ttl_input", "dma", "moninj"]}}
    csr = CSR(mapping)
    try:
        # Exercise an actual readable/writable register through PS->PL AXI.
        csr.write("rtio_target", 0x102)
        if csr.read("rtio_target") != 0x102:
            raise RuntimeError("PS-PL CSR readback failed")
        result["tests"]["ps_pl"] = {"status": "PASS"}
        before = csr.counter()
        start = time.monotonic()
        time.sleep(0.1)
        after = csr.counter()
        elapsed = time.monotonic() - start
        frequency = (after - before) / elapsed
        if after <= before:
            raise RuntimeError("RTIO counter does not advance")
        result["tests"]["rtio_counter"] = {"status": "PASS", "delta": after - before}
        if abs(frequency - 125e6) / 125e6 > 0.02:
            raise RuntimeError(f"Unexpected RTIO frequency: {frequency}")
        result["tests"]["clocks"] = {"status": "PASS", "estimated_rtio_hz": frequency,
                                     "method": "counter vs Linux monotonic clock, tolerance 2%"}
        csr.write("rtio_core_reset", 1)
        csr.write("rtio_core_reset_phy", 1)
        time.sleep(0.001)
        now = csr.counter()
        rise = now + 125000000
        width = 625000
        csr.event(1, 2, rise - 12500000, 3)  # both-edge input gate
        csr.event(0, 0, rise, 1)
        csr.event(0, 0, rise + width, 0)
        first = csr.input_event(rise + 125000000)
        second = csr.input_event(rise + 125000000)
        if [first[1], second[1]] != [1, 0] or abs(second[0] - first[0] - width) > 1:
            raise RuntimeError(f"TTL loopback mismatch: {first}, {second}")
        result["tests"]["ttl_input"] = {"status": "PASS", "events": [first, second]}
        result["tests"]["ttl_output"] = {"status": "PASS", "width_ticks": second[0] - first[0],
                                        "method": "physical TTL loopback; +/-1 input synchronizer tick"}
        csr.write("rtio_moninj_mon_chan_sel", 0)
        csr.write("rtio_moninj_mon_probe_sel", 0)
        time.sleep(0.001)
        csr.write("rtio_moninj_mon_value_update", 1)
        if csr.read("rtio_moninj_mon_value") != 0:
            raise RuntimeError("TTL output did not return low")
        result["tests"]["moninj"] = {"status": "PASS", "scope": "CSR probe only, network protocol pending"}
        if csr.read("rtio_core_async_error"):
            raise RuntimeError("RTIO asynchronous error")
    except Exception as error:
        result["failure"] = str(error)
    finally:
        csr.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csr-map", type=Path)
    parser.add_argument("--output", type=Path, default=Path("hardware-results.json"))
    options = parser.parse_args()
    if options.csr_map is None:
        result = {"kind": "hardware", "status": "NOT_RUN",
                  "reason": "Run on Genesys PS with --csr-map and JB1->JB2 jumper"}
    else:
        try:
            result = run(json.loads(options.csr_map.read_text()))
        except Exception as error:
            result = {"kind": "hardware", "status": "FAILED", "failure": str(error)}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result.get("status") == "NOT_RUN":
        return 2
    if result.get("status") == "FAILED" or "failure" in result:
        return 1
    # Unimplemented/not-run stages prevent the complete hardware suite passing.
    return 2 if any(test["status"] != "PASS" for test in result["tests"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
