#!/usr/bin/env python3
"""Run AUX firmware under inherited bounded wrapper lease; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import serial


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('server','port','elf','csr-map','output'):p.add_argument('--'+n,required=True)
    p.add_argument('--service',action='store_true')
    a=p.parse_args()
    lock=Path.home()/'.cache/genesys-210383B7F02DA.lock'
    fd=os.environ.get('GENESYS_LEASE_FD')
    if not fd:p.error('Requires test_drtio_aux_bringup.py inherited board lease')
    stat=os.fstat(int(fd));expected=lock.stat()
    if (stat.st_dev,stat.st_ino)!=(expected.st_dev,expected.st_ino):p.error('Wrong board lease')
    elf=Path(a.elf).resolve();build=json.loads((elf.parent/'results.json').read_text())
    if build.get('status')!='PASS' or build['elf_sha256']!=hashlib.sha256(elf.read_bytes()).hexdigest():
        p.error('Firmware build/hash mismatch')
    if build['csr_map_sha256']!=hashlib.sha256(Path(a.csr_map).read_bytes()).hexdigest():
        p.error('Firmware map mismatch')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    repo=Path(__file__).resolve().parents[3]
    raw=bytearray()
    with serial.Serial(a.port,115200,timeout=.2) as uart:
        uart.reset_input_buffer()
        cmd=['vivado-container','shell','-c','exec "$@"','bash',
             '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',
             str(repo/'scripts/run_ethernet.tcl'),a.server,str(elf),'210383B7F02DA']
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'load.log').write_text(run.stdout+run.stderr)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            raw.extend(uart.read(uart.in_waiting or 1))
            if b'TEST ARTIQ_AUX_FIRMWARE PASS' in raw or b'TEST ARTIQ_AUX_FIRMWARE FAIL' in raw or b'AUX_FW PANIC' in raw:break
        service_counts={}
        if a.service:
            def await_token(token,number):
                limit=time.monotonic()+10
                while raw.count(token.encode())<number:
                    if time.monotonic()>limit:raise RuntimeError('Service timeout: '+token)
                    raw.extend(uart.read(uart.in_waiting or 1))
            await_token('AUX_SERVICE READY',1)
            for cycle in range(3):
                for command,tokens in [
                    (b'e',['AUX_SERVICE RESPOND request=0 reply=1','AUX_SERVICE IGNORE reply=1']),
                    (b'd',['AUX_SERVICE RESPOND request=32 reply=33','AUX_SERVICE IGNORE reply=33']),
                    (b'c',['AUX_SERVICE DROP kind=-1']),
                    (b'u',['AUX_SERVICE DROP kind=-2']),
                    (b'r',['AUX_SERVICE DROP kind=2']),
                    (b'e',['AUX_SERVICE RESPOND request=0 reply=1','AUX_SERVICE IGNORE reply=1'])]:
                    uart.write(command);uart.flush()
                    for token in tokens:
                        service_counts[token]=service_counts.get(token,0)+1
                        await_token(token,service_counts[token])
            limit=time.monotonic()+.5
            while time.monotonic()<limit:raw.extend(uart.read(uart.in_waiting or 1))
    (out/'uart.log').write_bytes(raw)
    lines=raw.decode(errors='replace').splitlines()
    exchanges=[line for line in lines if line.startswith('AUX_FW EXCHANGE')]
    ok=(run.returncode==0 and b'TEST ARTIQ_AUX_FIRMWARE PASS' in raw and
        len(exchanges)==31 and b'AUX_FW BAD_CRC PASS' in raw and
        b'AUX_FW UNKNOWN_TYPE PASS' in raw and b'FAIL' not in raw and b'PANIC' not in raw)
    if a.service:
        ok=ok and all(raw.count(token.encode())==number for token,number in service_counts.items())
        ok=ok and b'AUX_SERVICE RX_ERROR' not in raw and b'AUX_SERVICE SEND_FAIL' not in raw
    result={'kind':'PHYSICAL_FIRMWARE' ,'status':'PASS' if ok else 'FAIL',
        'scope':'two laboratory AUX roles on one A53, upstream Rust packet codec/CRC over real GTH loopback',
        'exchanges':exchanges,'bad_crc':b'AUX_FW BAD_CRC PASS' in raw,
        'unknown_type':b'AUX_FW UNKNOWN_TYPE PASS' in raw,'elf_sha256':build['elf_sha256'],
        'uart_sha256':hashlib.sha256(raw).hexdigest(),'remote_kasli':'NOT_RUN',
        'production_satellite_rtio':'NOT_RUN','destination_status':'DOWN','persistent_service':'PASS' if a.service and ok else 'NOT_RUN',
        'service_counts':service_counts}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not ok:print(raw.decode(errors='replace'))
    return 0 if ok else 1


if __name__=='__main__':raise SystemExit(main())
