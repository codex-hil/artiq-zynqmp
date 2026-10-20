"""Generate checked clock restoration inputs without hardware access.

LGPL-3.0-or-later. A plan is not a physically validated restoration procedure.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--board',choices=['KASLI01','KASLI03'],default='KASLI03')
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--si-source', type=Path, required=True)
    parser.add_argument('--runtime-source', type=Path, required=True)
    parser.add_argument('--generated', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    source = args.si_source.read_text()
    if snapshot['si_source_sha256'] != hashlib.sha256(source.encode()).hexdigest():
        raise SystemExit('Driver changed since snapshot')
    if (snapshot.get('board')!=args.board or int(snapshot['dna'],16)!={'KASLI01':0x007865085f704854,'KASLI03':0x0048458a64b04854}[args.board] or snapshot['changed_registers']):
        raise SystemExit('Wrong board or unstable snapshot')
    if any(len(v) != 2 or v[0] != v[1] for v in snapshot['registers'].values()):
        raise SystemExit('Incomplete repeated snapshot')
    cfg = set((args.generated / 'rust-cfg').read_text().splitlines())
    if 'si5324_soft_reset' not in cfg:
        raise SystemExit('Unexpected hard-reset build; review its restoration requirements')
    runtime = args.runtime_source.read_text()
    if 'csr::crg::switch_done_read()' not in runtime or 'csr::gt_drtio::stable_clkin_write(1)' not in runtime:
        raise SystemExit('Runtime clock-switch path changed')
    registers = {int(k): values[0] for k, values in snapshot['registers'].items()}
    writable = sorted({int(r) for r in re.findall(r'\bwrite\((\d+)', source)} - {136})
    if not writable or any(r not in registers for r in writable):
        raise SystemExit('Writable registers not covered by snapshot')
    # Register136 carries commands; status129/130 and product ID134/135 are not replayed.
    assert not ({129, 130, 134, 135, 136} & set(writable))
    if registers[136] & 0xc0 or registers[130] & 1:
        raise SystemExit('Baseline reset/calibration active or PLL unlocked')
    plan = {
        'status': 'OFFLINE_PLAN_ONLY_HARDWARE_NOT_RUN', 'board': args.board,
        'snapshot_sha256': hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
        'reset_kind': 'soft-reset, register136 bit7; reset value-byte NACK allowed by upstream',
        'configuration_to_compare_then_restore': [{'register': r, 'value': registers[r]} for r in writable],
        'never_replay': [129, 130, 134, 135, 136],
        'calibration_if_configuration_changed': 'fresh ICAL136 bit6, never saved reset/ICAL command bits',
        'required_validation': ['exact DNA/diagnostic image under shared locks',
            'compare fresh baseline before mutation', 'bounded I2C retries with STOP on every failure',
            'readback configuration and product ID', 'PLL lock and independent output frequency',
            'restore previous mux/bus state'],
        'runtime_flow': ['first upload/B may soft-reset/setup PLL and initiate sys clock switch',
            'CPU restarts at BRAM0; wait CRC/DDR/netboot again',
            'second upload/B uses switch_done and skips PLL setup',
            'validate runtime/services before any remote DRTIO claim'],
        'runtime_locks': (['genesys-210383B7F02DA','kasli-KASLI01'] if args.board=='KASLI01' else ['genesys-210383B7F02DA', 'kasli-KASLI01', 'kasli-KASLI02', 'kasli-KASLI03']),
        'reason_genesys_lock': 'runtime enables downstream TX; user cable connects Genesys',
        'i2c_reliability': snapshot.get('i2c_reliability','Read snapshot only; write reliability unqualified'),
        'restoration_validated': False
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + '\n')
    print(json.dumps({'status': plan['status'], 'configuration_registers': len(writable), 'reset_kind': plan['reset_kind']}))


if __name__ == '__main__':
    main()
