#!/usr/bin/env python3
"""Compare independent SPD bytes with DDRC snapshot; LGPL-3.0-or-later."""
import argparse,hashlib,json
from pathlib import Path
from decode_ddr4_spd import decode as spd_decode
from decode_ddr_config import decode as config_decode
from decode_ddr_addrmap import geometry


def compare(spd_bytes,snapshot):
    spd=spd_decode(spd_bytes);controller=geometry(config_decode(snapshot)['registers'])
    pairs=[('row_bits','row_bits'),('column_bits','column_bits'),('bank_bits','bank_bits'),
           ('bank_group_bits','bank_group_bits'),('ranks','active_ranks'),
           ('primary_bus_bits','data_bus_bits'),('module_bytes','programmed_bytes')]
    fields={left:dict(spd=spd[left],controller=controller[right],equal=spd[left]==controller[right]) for left,right in pairs}
    match=all(v['equal'] for v in fields.values())
    return dict(status='GEOMETRY_MATCH_CRC_AND_ACQUISITION_NOT_VERIFIED' if match else 'GEOMETRY_MISMATCH',
                geometry_matches=match,fields=fields,hardware_executed=False,crc='NOT_VERIFIED',
                spd_sha256=hashlib.sha256(spd_bytes).hexdigest(),snapshot_sha256=hashlib.sha256(snapshot.encode()).hexdigest(),
                physical_capacity='NOT_VERIFIED',destructive_test_allowed=False,
                limits='Compares provided inputs only, including synthetic inputs. Does not prove EEPROM origin/CRC, CPU address windows, alias freedom, quiescence or memory integrity.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('spd','snapshot','output'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    result=compare(a.spd.read_bytes(),a.snapshot.read_text())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0 if result['geometry_matches'] else 1

if __name__=='__main__':raise SystemExit(main())
