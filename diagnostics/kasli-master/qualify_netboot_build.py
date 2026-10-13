"""Qualify completed netboot build artifacts, never access hardware.

LGPL-3.0-or-later. Timing closure does not establish physical operation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    source = args.source.resolve()
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != '486e8f897547d282d46a02c30463449c21e30cfe':
        raise SystemExit('Wrong upstream revision')
    patch = subprocess.check_output(['git', '-C', str(source), 'diff'], text=True)
    if patch != (repo / 'diagnostics/kasli-master/kasli03-netboot.patch').read_text():
        raise SystemExit('Netboot overlay differs from reviewed patch')
    config = json.loads((args.build / 'config.json').read_text())
    if (config['hw_rev'], config['drtio_role'], config['rtio_frequency'], config['peripherals']) != ('v1.1', 'master', 125000000, []):
        raise SystemExit('Unexpected board configuration')
    tree = args.build / 'generated/genesys_drtio_master_v11'
    variables = (tree / 'software/include/generated/variables.mak').read_text()
    if f'BOOTLOADER_DIRECTORY={source}/artiq/firmware/bootloader\n' not in variables:
        raise SystemExit('Build did not select the reviewed bootloader source')
    gate = tree / 'gateware'
    if 'synth_design -top top -part xc7a100t-fgg484-2' not in (gate / 'top_route.tcl').read_text():
        raise SystemExit('Wrong FPGA part')
    timing = (gate / 'top_timing.rpt').read_text()
    if 'All user specified timing constraints are met.' not in timing:
        raise SystemExit('Timing not closed')
    match = re.search(r'\n\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+)\s+(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+)\s+(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+)\s+(\d+)\s*\n', timing)
    if not match or any(int(match[i]) for i in (3, 7, 11)):
        raise SystemExit('Timing summary missing or violating endpoints present')
    drc = (gate / 'top_drc.rpt').read_text()
    if re.search(r'^\S+#\d+\s+(?:Error|Critical Warning)\s*$', drc, re.M):
        raise SystemExit('DRC error/critical warning requires review')
    hashes = {}
    for name in ('gateware/top.bit', 'gateware/top.bin', 'software/bootloader/bootloader.bin',
                 'software/runtime/runtime.bin', 'software/runtime/runtime.elf', 'software/runtime/runtime.fbi'):
        data = (tree / name).read_bytes()
        if not data:
            raise SystemExit(f'Empty artifact: {name}')
        hashes[name] = hashlib.sha256(data).hexdigest()
    # The completed build script emits this only after Vivado and artifact checks.
    if not (args.build / 'artifacts.sha256').is_file():
        raise SystemExit('Build completion marker absent')
    result = {'status': 'BUILD_PASS_HARDWARE_NOT_RUN', 'boot_mode': 'network-only',
              'bit_sha256': hashes['gateware/top.bit'], 'artifact_hashes': hashes,
              'upstream_revision': revision, 'overlay_sha256': hashlib.sha256(patch.encode()).hexdigest(),
              'setup_wns_ns': float(match[1]), 'hold_whs_ns': float(match[5]),
              'pulse_slack_ns': float(match[9]), 'network': 'IPv6 link-local; bootloader has no DHCP client',
              'limitations': ['inherited external timing warnings', 'no physical qualification'],
              'build': str(args.build.resolve())}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
