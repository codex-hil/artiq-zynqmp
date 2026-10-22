#!/usr/bin/env python3
"""Decode fixed DDRC configuration snapshot, not fitted capacity; LGPL-3.0-or-later."""
import argparse,hashlib,json,re
from pathlib import Path
REGISTERS=dict(MSTR=0xfd070000,ECCCFG0=0xfd070070,**{'ADDRMAP'+str(i):0xfd070200+4*i for i in range(12)})


def decode(text):
    rows=re.findall(r'^DDR_CONFIG (\w+) (0x[0-9a-fA-F]+) (0x[0-9a-fA-F]+)$',text,re.M);values={}
    for name,address,value in rows:
        if name not in REGISTERS or int(address,16)!=REGISTERS[name] or name in values or int(value,16)>0xffffffff:raise ValueError('Unexpected/duplicate DDR configuration register')
        values[name]=int(value,16)
    if set(values)!=set(REGISTERS) or 'TEST ddr_config_snapshot PASS' not in text:raise ValueError('Incomplete DDR configuration capture')
    m=values['MSTR'];ranks=(m>>24)&3;width=(m>>12)&3
    if ranks not in (1,3) or width==3:raise ValueError('Reserved rank/bus-width configuration')
    return dict(status='CONTROLLER_CONFIGURATION_DECODED_NOT_CAPACITY_PROOF',hardware_executed=False,
        ddr4=bool(m&16),active_rank_mask=ranks,active_ranks=ranks.bit_count(),device_dq_bits=4<<((m>>30)&3),
        bus_width_proportion=['full','half','quarter'][width],ecc_mode=values['ECCCFG0']&7,
        registers={k:hex(v) for k,v in values.items()},physical_capacity='NOT_ESTABLISHED',
        limits='DDRC programmed fields only; no SPD capture, full address-map reconstruction, physical alias test or writable DDR interval authorization.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--log',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output report')
    r=decode(a.log.read_text());r['input_sha256']=hashlib.sha256(a.log.read_bytes()).hexdigest();a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))

if __name__=='__main__':main()
