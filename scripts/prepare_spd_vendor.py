#!/usr/bin/env python3
"""Prepare isolated, auditable AMD receive bounds; LGPL-3.0-or-later."""
import argparse,difflib,hashlib,json
from pathlib import Path

def patch(name,text):
    changes={
      'xiicps_hw.c':('\twhile ((XIicPs_RxDataValid(InstancePtr)) != 0U) {',
        '\twhile ((InstancePtr->RecvByteCount > 0) &&\n\t       ((XIicPs_RxDataValid(InstancePtr)) != 0U)) {'),
      'xiicps_master.c':('\tXIicPs_MasterIntrRead(InstancePtr, &IntrStatusReg, IsHold);',
        '\tXIicPs_MasterIntrRead(InstancePtr, &IntrStatusReg, IsHold);\n\n'
        '\t/* Local SPD diagnostic guard: exhausted buffer with residual FIFO data. */\n'
        '\tif ((InstancePtr->IsSend == 0) && (InstancePtr->RecvByteCount == 0) &&\n'
        '\t    ((XIicPs_ReadReg(BaseAddr, XIICPS_SR_OFFSET) & XIICPS_SR_RXDV_MASK) != 0U)) {\n'
        '\t\tStatusEvent |= XIICPS_EVENT_ERROR;\n\t}')}
    if name not in changes:return text
    old,new=changes[name]
    if text.count(old)!=1:raise ValueError('Vendor source drift: '+name)
    return text.replace(old,new)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bsp',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    root=a.bsp/'libsrc/iicps/src';pending={}
    for name in ('xiicps_hw.c','xiicps_master.c','xiicps_xfer.c'):
        original=(root/name).read_text();pending[name]=(original,patch(name,original))
    a.output.mkdir(parents=True);manifest={};diff=[]
    for name,(old,new) in pending.items():
        (a.output/name).write_text(new)
        manifest[name]=dict(input_path=str(root/name),input_sha256=hashlib.sha256(old.encode()).hexdigest(),output_sha256=hashlib.sha256(new.encode()).hexdigest())
        diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original/'+name,tofile='local/'+name))
    (a.output/'receive-bounds.patch').write_text(''.join(diff))
    (a.output/'manifest.json').write_text(json.dumps(dict(status='COPIED_SOURCE_PREPARED_NOT_HARDWARE_ADMISSION',files=manifest),indent=2)+'\n')
if __name__=='__main__':main()
