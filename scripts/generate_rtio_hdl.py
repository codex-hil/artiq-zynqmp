#!/usr/bin/env python3
"""Emit the real RTIO/AXI subsystem HDL without invoking Vivado or PS IP.

This is a subsystem artifact, not a board bitstream or a substitute for XSA.
"""
import argparse
import os
from pathlib import Path
import sys

from migen import Signal
from migen.fhdl import verilog

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "boards/genesys_zu-5ev/1_gateware"))
from local_rtio import LocalRTIO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    os.chdir(options.output.resolve())
    output = Signal(name="ttl_out")
    input_ = Signal(name="ttl_in")
    dut = LocalRTIO(output, input_)
    ios = {output, input_}
    for channel in ["aw", "w", "b", "ar", "r"]:
        ios.update(getattr(dut.axi, channel).flatten())
    generated = verilog.convert(dut, ios=ios, name="genesys_local_rtio")
    generated.write("local_rtio.v")
    dut.write_map("csr-map.json")
    print("Generated subsystem HDL and CSR map; FPGA synthesis not run")


if __name__ == "__main__":
    main()
