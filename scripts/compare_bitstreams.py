#!/usr/bin/env python3
"""Compare x4k .bit configuration bytes, separately from metadata; LGPL-3.0-or-later.

Format reference: AMD bootgen common/src/bitutils.cpp ReadBITHeader_x4k.
Does not establish hardware behavior or equivalence of different payloads.
"""
import argparse,hashlib,json,struct
from pathlib import Path


def parse(data):
    offset=0
    def take(n):
        nonlocal offset
        if n<0 or offset+n>len(data):raise ValueError('Truncated bitstream')
        value=data[offset:offset+n];offset+=n;return value
    def short():return struct.unpack('>H',take(2))[0]
    def string():return take(short())
    if string()!=bytes.fromhex('0ff00ff00ff00ff000') or short()!=1:raise ValueError('Unsupported .bit preamble')
    fields={}
    for tag,name in zip(b'abcd',('design','device','date','time')):
        if take(1)!=bytes([tag]):raise ValueError('Unexpected .bit field')
        raw=string()
        if not raw.endswith(b'\0') or not raw[:-1]:raise ValueError('Invalid .bit string')
        fields[name]=raw[:-1].decode('ascii')
    if take(1)!=b'e':raise ValueError('Missing configuration payload')
    size=struct.unpack('>I',take(4))[0]
    if size<=0 or size%4:raise ValueError('Invalid configuration length')
    payload=take(size)
    if offset!=len(data):raise ValueError('Unexpected trailing bitstream bytes')
    return fields,payload


def compare(left,right):
    a,ap=parse(left);b,bp=parse(right)
    return dict(status='CONFIGURATION_BYTES_IDENTICAL' if ap==bp else 'CONFIGURATION_BYTES_DIFFER',hardware_executed=False,
                full_files_identical=left==right,metadata=dict(left=a,right=b),payload_bytes=dict(left=len(ap),right=len(bp)),
                payload_sha256=dict(left=hashlib.sha256(ap).hexdigest(),right=hashlib.sha256(bp).hexdigest()),
                scope='Exact raw FPGA configuration bytes; header metadata reported separately. No new physical test.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('left',type=Path);p.add_argument('right',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Refusing to overwrite report')
    result=compare(a.left.read_bytes(),a.right.read_bytes())
    result['files']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (a.left,a.right)}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
