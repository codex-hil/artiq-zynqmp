#!/usr/bin/env python3
"""Check actual executable metadata; a zero-entry ELF is not bootable."""
import argparse
import json
from pathlib import Path
import struct


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument("--memory", choices=["ddr", "ocm"], default="ddr")
    options = parser.parse_args()
    lower, upper = (0xFFFC0000, 0x100000000) if options.memory == "ocm" else (0x100000, 0x1100000)
    data = options.elf.read_bytes()
    if data[:6] != b"\x7fELF\x02\x01":
        raise ValueError("Expected little-endian ELF64")
    fields = struct.unpack_from("<HHIQQQIHHHHHH", data, 16)
    etype, machine, version, entry, phoff, _, _, _, phsize, phcount, *_ = fields
    if etype != 2 or machine != 183 or entry == 0:
        raise ValueError("Invalid AArch64 executable or zero entry point")
    segments = []
    executable_entry = False
    for index in range(phcount):
        ptype, flags, offset, vaddr, paddr, filesz, memsz, align = struct.unpack_from(
            "<IIQQQQQQ", data, phoff + index * phsize)
        if ptype != 1:
            continue
        if not (lower <= paddr and paddr + memsz <= upper):
            raise ValueError("Segment outside exclusively reserved diagnostic memory range")
        if filesz > memsz or offset + filesz > len(data):
            raise ValueError("Invalid load segment")
        executable_entry |= bool(flags & 1 and vaddr <= entry < vaddr + filesz)
        segments.append({"address": paddr, "file_bytes": filesz, "memory_bytes": memsz, "flags": flags})
    if not executable_entry:
        raise ValueError("ELF entry is not in executable file-backed code")
    print(json.dumps({"kind": "software-validation", "status": "PASS",
                      "entry": entry, "segments": segments}, indent=2))


if __name__ == "__main__":
    main()
