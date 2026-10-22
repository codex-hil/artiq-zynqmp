#!/usr/bin/env python3
"""Offline configured DDR/ELF map audit, never a write authorization; LGPL-3.0-or-later."""
import argparse,hashlib,json,re
from pathlib import Path
from package_local_candidate import loads


def banks(text):
    result=[]
    for name in ('psu_ddr_0','psu_ddr_1'):
        node=re.search(r'\b'+name+r':\s*[^\{]+\{([^}]+)\}',text)
        if not node:raise ValueError('Missing configured DDR node: '+name)
        reg=re.search(r'\breg\s*=\s*<([^>]+)>',node[1])
        if not reg:raise ValueError('Missing DDR reg')
        cells=[int(v,0) for v in reg[1].split()]
        if not cells or len(cells)%4 or any(v<0 or v>0xffffffff for v in cells):raise ValueError('Invalid 64-bit DDR reg cells')
        for i in range(0,len(cells),4):
            start=(cells[i]<<32)|cells[i+1];size=(cells[i+2]<<32)|cells[i+3]
            if not size or start+size>1<<64 or start%64 or size%64:raise ValueError('Invalid DDR interval')
            result.append((start,start+size))
    result.sort();merged=[]
    for lo,hi in result:
        if merged and lo<merged[-1][1]:raise ValueError('Overlapping configured DDR intervals')
        if merged and lo==merged[-1][1]:merged[-1]=(merged[-1][0],hi)
        else:merged.append((lo,hi))
    return merged


def inventory(pcw,manifest):
    configured=banks(pcw.read_text());m=json.loads(manifest.read_text());segments=[]
    for role in ('candidate_cpu0','candidate_worker','candidate_bridge'):
        item=m['files'][role];path=Path(item['path']);data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Changed ELF: '+role)
        machine,entry,parts=loads(data)
        for p in parts:
            if p['memsz']:
                segments.append(dict(role=role,machine=machine,entry=hex(entry),start=hex(p['address']),end_exclusive=hex(p['address']+p['memsz']),file_bytes=p['filesz'],memory_bytes=p['memsz']))
    return dict(status='OFFLINE_DDR_MAP_INVENTORY_NOT_EXECUTABLE',hardware_executed=False,
        configured_banks=[dict(start=hex(lo),end_exclusive=hex(hi),bytes=hi-lo) for lo,hi in configured],
        configured_bytes=sum(hi-lo for lo,hi in configured),physical_capacity='NOT_VERIFIED_FROM_SPD_OR_CONTROLLER',
        occupied_elf_segments=segments,additional_runtime_use=['CPU0 upload/RPC input at0x21000000 up to1MiB','DMA trace storage and kernel/runtime heaps','PS/PL AXI DMA and other active masters'],
        destructive_test_allowed=False,
        requirements=['Verify actual SPD/controller address map under shared Genesys lease','Use exclusive OCM-resident diagnostic with verified ELF/stack/page tables outside tested DDR','Park other CPUs/R5 and disable PL/peripheral DDR masters using a reviewed load/restoration flow','Verify cache/MMU attributes; do not let cache-only reads pass as DDR','Bound UART progress and test duration; restore baseline and validate after every window'],
        proposed_stages=['small uncached interval/address-data tests','bounded chunk sweep with address-derived/complement patterns','cross-bank alias/address-line controls','separate cache-maintained sustained workload'],
        limits='Configured windows are not fitted memory proof. ELF inventory does not enumerate all live allocations or prove any range safe while runtime is active.',
        input_sha256={str(pcw):hashlib.sha256(pcw.read_bytes()).hexdigest(),str(manifest):hashlib.sha256(manifest.read_bytes()).hexdigest()})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pcw',required=True,type=Path);p.add_argument('--manifest',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output path')
    report=inventory(a.pcw,a.manifest);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
