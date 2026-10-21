#!/usr/bin/env python3
"""Read plain ZynqMP PHTs and compare CPU payloads; LGPL-3.0-or-later.

Layout follows AMD bootgen zynqmp/include/{bootheader,partitionheadertable}-zynqmp.h.
Checks packaged bytes only, not execution, BSS initialization, PL or PMU payloads.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from package_local_candidate import loads


def partitions(data):
    if len(data)<0xa0 or struct.unpack_from('<II',data,0x20)!=(0xaa995566,0x584c4e58):
        raise ValueError('Not a supported ZynqMP boot header')
    offset=struct.unpack_from('<I',data,0x9c)[0];seen=set();result=[]
    while offset:
        if offset in seen or len(seen)>=64 or offset%4 or offset<0xa0 or offset+64>len(data):
            raise ValueError('Invalid/cyclic partition header chain')
        seen.add(offset);words=struct.unpack_from('<16I',data,offset)
        if sum(words)&0xffffffff!=0xffffffff:raise ValueError('Partition header checksum mismatch')
        encrypted,plain,total,next_word=words[:4];attributes=words[9]
        if attributes&((1<<7)|(1<<15)) or (attributes>>12)&7 or encrypted!=plain:
            raise ValueError('Only plain unauthenticated/no-checksum partitions supported')
        start=words[8]*4;length=plain*4
        if total<plain or start+total*4>len(data) or start<0xa0:
            raise ValueError('Partition payload outside boot image')
        result.append(dict(header_offset=offset,partition_number=words[14],address=words[6]|words[7]<<32,
            entry=words[4]|words[5]<<32,cpu=(attributes>>8)&15,device=(attributes>>4)&7,
            offset=start,bytes=length,payload=data[start:start+length]))
        offset=next_word*4
    if not result:raise ValueError('No partitions')
    return result


def match(parts,segments,cpu,label):
    result=[]
    for segment in segments:
        if not segment['filesz']:continue
        candidates=[p for p in parts if p['device']==1 and p['cpu']==cpu and p['address']==segment['address']]
        if len(candidates)!=1:raise ValueError('Missing/ambiguous CPU partition: '+label)
        p=candidates[0];payload=segment['payload'];padding=p['payload'][len(payload):]
        if p['bytes']!=(len(payload)+3)//4*4 or p['payload'][:len(payload)]!=payload or any(padding):
            raise ValueError('Serialized CPU payload mismatch: '+label)
        result.append(dict(label=label,address=hex(p['address']),bytes=len(payload),partition_number=p['partition_number'],
                           image_offset=p['offset'],sha256=hashlib.sha256(payload).hexdigest()))
    if not result:raise ValueError('No file-backed segments: '+label)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Refusing to overwrite report')
    image=(a.package/'BOOT.BIN').read_bytes();digest=hashlib.sha256(image).hexdigest()
    if digest!=json.loads((a.package/'release.json').read_text())['boot_bin_sha256']:raise ValueError('BOOT.BIN digest mismatch')
    artifacts=json.loads((a.package/'artifacts.json').read_text())['artifacts'];parts=partitions(image);verified=[]
    for role,cpu,machine in [('worker_boot',2,183),('application',1,183)]:
        artifact=Path(artifacts[role]['path']);data=artifact.read_bytes()
        if hashlib.sha256(data).hexdigest()!=artifacts[role]['sha256']:raise ValueError('Changed input ELF')
        actual,entry,segments=loads(data)
        if actual!=machine:raise ValueError('Wrong input machine')
        verified+=match(parts,segments,cpu,role)
    report=dict(status='SERIALIZED_CPU_PAYLOADS_PASS',hardware_executed=False,cold_boot='NOT_RUN',
        boot_bin_sha256=digest,partition_headers_checked=len(parts),cpu_payloads=verified,
        scope='PHT chain/checksums/bounds and file-backed CPU0/CPU1 payloads only. FSBL/PMU/PL payload equality, BSS initialization and execution are not established.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
