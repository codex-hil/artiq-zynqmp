#!/usr/bin/env python3
"""Strict FSBL diagnostic base-SPD log extraction and CRC gate; LGPL-3.0-or-later."""
import argparse,hashlib,json,re
from pathlib import Path
from check_ddr4_spd_crc import verify
from decode_ddr4_spd import decode

def extract(text):
    begin='SPD_BASE_BEGIN bytes=128';end='SPD_BASE_END'
    lines=[s.strip() for s in text.splitlines()]
    if lines.count(begin)!=1 or lines.count(end)!=1:raise ValueError('Require one complete SPD frame')
    lo=lines.index(begin);hi=lines.index(end)
    if hi<=lo or hi-lo!=9:raise ValueError('Malformed SPD frame length/order')
    data=bytearray()
    for index,line in enumerate(lines[lo+1:hi]):
        match=re.fullmatch(r'SPD_BASE (\d{3}) ([0-9a-fA-F]{32})',line)
        if not match or int(match[1])!=index*16:raise ValueError('Malformed/duplicate/out-of-order SPD row')
        data.extend(bytes.fromhex(match[2]))
    if any(s.startswith('SPD_BASE ') for s in lines[:lo]+lines[hi+1:]):raise ValueError('SPD rows outside frame')
    if not any('Exit from FSBL' in s for s in lines[hi+1:]):raise ValueError('FSBL completion missing after SPD')
    report=verify(data)
    if not report['valid']:raise ValueError('SPD base CRC mismatch')
    return bytes(data),dict(status='FSBL_SPD_FRAME_CRC_VALID_ACQUISITION_NOT_PROVEN',
        hardware_executed=False,log_sha256=hashlib.sha256(text.encode()).hexdigest(),
        crc=report,geometry=decode(data,require_crc=True),destructive_test_allowed=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--log',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output directory')
    data,report=extract(a.log.read_text());a.output.mkdir(parents=True)
    (a.output/'spd-base.bin').write_bytes(data);(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
