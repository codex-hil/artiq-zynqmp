#!/usr/bin/env python3
"""Verify OCM ELF/layout boundaries, not execution state; LGPL-3.0-or-later."""
import argparse,hashlib,json,re
from pathlib import Path
from package_local_candidate import loads
BASE=0xfffc0000
END=0x100000000


def check(data,symbol_text):
    machine,entry,segments=loads(data)
    if machine!=183 or not BASE<=entry<END:raise ValueError('Not an AArch64 OCM entry')
    if not segments or any(s['address']<BASE or s['address']+s['memsz']>END or s['vaddr']!=s['address'] for s in segments):raise ValueError('ELF load/memory segment outside identity-mapped OCM')
    if not any(s['flags']&1 and s['address']<=entry<s['address']+s['filesz'] for s in segments):raise ValueError('Entry is not in executable file-backed OCM')
    symbols={name:int(address,16) for address,name in re.findall(r'^([0-9a-fA-F]+)\s+\w\s+(\S+)$',symbol_text,re.M)}
    required=['__ocm_start','__vectors','__bss_start','__bss_end','__stack0_end']
    if any(n not in symbols or not BASE<=symbols[n]<=END for n in required):raise ValueError('Missing/out-of-OCM layout symbol')
    stack_end=symbols['__stack0_end'];stack_start=stack_end-0x4000
    if entry!=symbols['__ocm_start'] or symbols['__vectors']%2048 or not BASE<=symbols['__bss_start']<=symbols['__bss_end']<=stack_start<stack_end<=END:
        raise ValueError('Unexpected OCM vector/BSS/16KiB-stack layout')
    if not any(s['address']<=stack_start and stack_end<=s['address']+s['memsz'] for s in segments):raise ValueError('Stack absent from ELF memory extent')
    return dict(status='OCM_IMAGE_LAYOUT_PASS_EXECUTION_STATE_NOT_PROVEN',hardware_executed=False,
        entry=hex(entry),load_segments=[dict(start=hex(s['address']),end_exclusive=hex(s['address']+s['memsz']),file_bytes=s['filesz'],flags=s['flags']) for s in segments],
        stack=dict(start=hex(stack_start),end_exclusive=hex(stack_end)),
        mmu_cache_state='NOT_PROVEN',destructive_ddr_test_allowed=False,
        limits='Checks selected linker symbol/layout convention only. Does not establish live EL/SCTLR/cache state, stack use, parked cores, DMA masters or valid DDR intervals.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',required=True,type=Path);p.add_argument('--symbols',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    r=check(a.elf.read_bytes(),a.symbols.read_text());r['input_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.elf,a.symbols)};a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))

if __name__=='__main__':main()
