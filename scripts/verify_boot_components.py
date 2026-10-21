#!/usr/bin/env python3
"""Verify plain ZynqMP serialized PMU/FSBL/PL bytes; LGPL-3.0-or-later.

AMD bootgen CombineElfSections/AttachPmuFw layout; no execution proof.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from package_local_candidate import loads
from compare_bitstreams import parse
from verify_boot_payloads import partitions


def digest(data):return hashlib.sha256(data).hexdigest()


def combine(data,machine):
    actual,entry,segments=loads(data)
    if actual!=machine:raise ValueError('Wrong boot firmware ELF machine')
    segments=[s for s in segments if s['filesz']]
    if not segments:raise ValueError('No firmware payload')
    base=segments[0]['address'];end=base;result=bytearray()
    for s in segments:
        if s['address']<end or s['address']+s['filesz']-base>0x40000:
            raise ValueError('Overlapping/unsorted/oversized boot firmware')
        result.extend(bytes(s['address']-end));result.extend(s['payload']);end=s['address']+s['filesz']
    return base,entry,bytes(result)


def pl_payload(bit):
    _,payload=parse(bit)
    return b''.join(payload[i:i+4][::-1] for i in range(0,len(payload),4))


def verify(image,fsbl,pmu,bit):
    parts=partitions(image)
    if sum(struct.unpack_from('<11I',image,0x20))&0xffffffff!=0xffffffff:
        raise ValueError('Boot header checksum mismatch')
    entry,start,pmulen,pmutotal,fsbllen,fsbltotal=struct.unpack_from('<6I',image,0x2c)
    fb,fe,f=combine(fsbl,183);pb,pe,p=combine(pmu,189)
    p+=bytes((-len(p))%4)
    if pmulen!=pmutotal or fsbllen!=fsbltotal or pmulen!=len(p) or fsbllen!=len(f) or entry!=fe:
        raise ValueError('Boot header firmware lengths/entry mismatch')
    first=parts[0]
    if first['device']!=1 or first['cpu']!=1 or first['offset']!=start or first['address']!=fb or first['entry']!=fe or first['bytes']!=len(p)+len(f):
        raise ValueError('Combined boot firmware partition layout mismatch')
    if first['payload']!=p+f:raise ValueError('Serialized PMU/FSBL payload mismatch')
    pl=[part for part in parts if part['device']==2]
    expected=pl_payload(bit)
    if len(pl)!=1 or pl[0]['payload']!=expected:raise ValueError('Serialized PL payload mismatch')
    return dict(status='SERIALIZED_BOOT_COMPONENTS_PASS',hardware_executed=False,cold_boot='NOT_RUN',
        pmufw=dict(image_offset=start,bytes=len(p),elf_load_base=hex(pb),elf_entry=hex(pe),sha256=digest(p)),
        fsbl=dict(image_offset=start+len(p),bytes=len(f),elf_load_base=hex(fb),elf_entry=hex(fe),sha256=digest(f)),
        pl=dict(image_offset=pl[0]['offset'],bytes=len(expected),transformation='Reverse bytes within each 32-bit .bit payload word',sha256=digest(expected)),
        scope='Exact serialized file-backed bytes with bootgen gap/padding/byte-order rules. Not BSS initialization, execution, secure boot or cold boot.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--package',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);a=parser.parse_args()
    if a.output.exists():raise ValueError('Use fresh output report')
    artifacts=json.loads((a.package/'artifacts.json').read_text())['artifacts'];data={}
    for role in ('fsbl','pmufw','bitstream'):
        data[role]=Path(artifacts[role]['path']).read_bytes()
        if digest(data[role])!=artifacts[role]['sha256']:raise ValueError('Changed artifact: '+role)
    image=(a.package/'BOOT.BIN').read_bytes()
    if digest(image)!=artifacts['boot.bin']['sha256']:raise ValueError('Changed BOOT.BIN')
    report=verify(image,data['fsbl'],data['pmufw'],data['bitstream']);report['boot_bin_sha256']=digest(image)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
