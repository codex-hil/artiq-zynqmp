#!/usr/bin/env python3
"""Package real, matching ZynqMP artifacts using open-source AMD bootgen.

Does not produce FSBL/PMU firmware or a bitstream. The caller must provide
artifacts for the same board and PS configuration. No programming is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["fsbl", "bitstream", "application"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--pmufw", type=Path)
    parser.add_argument("--worker-boot", type=Path,
                        help="AArch64 CPU1 bridge ELF containing the AArch32 worker")
    parser.add_argument("--bootgen", default="bootgen")
    parser.add_argument("--output-dir", type=Path, required=True)
    options = parser.parse_args()
    paths = {name: getattr(options, name).resolve() for name in
             ["fsbl", "bitstream", "application"]}
    if options.pmufw is not None:
        paths["pmufw"] = options.pmufw.resolve()
    if options.worker_boot is not None:
        if options.pmufw is None:
            parser.error("CPU1 boot requires --pmufw")
        paths["worker_boot"] = options.worker_boot.resolve()
    hashes = {}
    for name, path in paths.items():
        payload = path.read_bytes()
        if len(payload) < 64 or any(c in str(path) for c in ['"', '\n', '\r']):
            raise ValueError("Invalid artifact: " + str(path))
        if name != "bitstream" and payload[:4] != b"\x7fELF":
            raise ValueError("Expected ELF: " + str(path))
        hashes[name] = {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest()}
    output = options.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    bif = output / "boot.bif"
    bif.write_text('the_ROM_image:\n{\n' +
        f'  [bootloader, destination_cpu=a53-0] "{paths["fsbl"]}"\n' +
        (f'  [pmufw_image] "{paths["pmufw"]}"\n' if "pmufw" in paths else '') +
        f'  [destination_device=pl] "{paths["bitstream"]}"\n' +
        (f'  [destination_cpu=a53-1, exception_level=el-3] "{paths["worker_boot"]}"\n'
         if "worker_boot" in paths else '') +
        f'  [destination_cpu=a53-0, exception_level=el-3] "{paths["application"]}"\n' +
        '}\n')
    subprocess.run([options.bootgen, "-arch", "zynqmp", "-image", str(bif),
                    "-w", "-o", str(output / "boot.bin")], check=True)
    hashes["boot.bin"] = {"sha256": hashlib.sha256((output / "boot.bin").read_bytes()).hexdigest()}
    (output / "artifacts.json").write_text(json.dumps({
        "kind": "packaged-artifacts-not-boot-proof", "artifacts": hashes,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
