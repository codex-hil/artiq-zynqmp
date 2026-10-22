#!/usr/bin/env python3
"""Invert Piotr/AMD single-rank full-width DDR4 ADDRMAP; LGPL-3.0-or-later."""
import argparse,hashlib,json
from pathlib import Path
from decode_ddr_config import decode


def geometry(registers):
    r={k:int(v,0) if isinstance(v,str) else v for k,v in registers.items()}
    m=r['MSTR']
    if not m&16 or ((m>>24)&3)!=1 or ((m>>12)&3)!=0 or r['ADDRMAP0']&31!=31:
        raise ValueError('Only captured DDR4/single-rank/full64-bit mapping supported')
    if (r['ADDRMAP5']>>16)&15!=15:raise ValueError('Grouped row2..10 mapping not supported')
    groups={'column':[(0,0),(1,1)],'bank':[],'bank_group':[],'row':[]}
    def fields(kind,register,indices,mask,base,disabled):
        for shift,index in enumerate(indices):
            value=(r['ADDRMAP'+str(register)]>>(shift*8))&mask
            if value!=disabled:groups[kind].append((index,base(index)+value))
    fields('column',2,range(2,6),15,lambda i:i,15)
    fields('column',3,range(6,10),15,lambda i:i,15)
    fields('column',4,range(10,12),15,lambda i:i,15)
    fields('bank',1,range(3),31,lambda i:i+2,31)
    fields('bank_group',8,range(2),31,lambda i:i+2,31)
    # AMD's row2..10 override registers are used when ADDRMAP5's group is15.
    fields('row',5,[0,1],15,lambda i:i+6,15)
    value=(r['ADDRMAP5']>>24)&15
    if value!=15:groups['row'].append((11,17+value))
    fields('row',6,range(12,16),15,lambda i:i+6,15)
    fields('row',7,range(16,18),15,lambda i:i+6,15)
    fields('row',9,range(2,6),15,lambda i:i+6,15)
    fields('row',10,range(6,10),15,lambda i:i+6,15)
    fields('row',11,[10],15,lambda i:i+6,15)
    hif={}
    for kind,entries in groups.items():
        entries.sort()
        if not entries or [i for i,_ in entries]!=list(range(len(entries))):raise ValueError('Missing/noncontiguous '+kind+' bits')
        for index,bit in entries:
            if bit in hif or bit<0 or bit>=40:raise ValueError('Colliding/out-of-range HIF bit')
            hif[bit]=kind+str(index)
    if sorted(hif)!=list(range(len(hif))):raise ValueError('Gaps in HIF mapping')
    return dict(status='PROGRAMMED_HIF_GEOMETRY_DECODED_NOT_PHYSICAL_PROOF',row_bits=len(groups['row']),column_bits=len(groups['column']),bank_bits=len(groups['bank']),bank_group_bits=len(groups['bank_group']),active_ranks=1,data_bus_bits=64,hif_bits=len(hif),programmed_bytes=1<<(len(hif)+3),hif_to_dram={str(k):hif[k] for k in sorted(hif)},physical_capacity='NOT_VERIFIED',destructive_test_allowed=False,
        limits='Limited to Piotr/AMD individually mapped row-bit mode, single rank/full width. Does not prove CPU physical-window remapping, SPD geometry, alias freedom or memory integrity.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    capture=decode(a.snapshot.read_text());result=geometry(capture['registers']);result['hardware_executed']=False
    result['snapshot_sha256']=hashlib.sha256(a.snapshot.read_bytes()).hexdigest();a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
