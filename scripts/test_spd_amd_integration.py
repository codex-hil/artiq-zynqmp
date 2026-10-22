#!/usr/bin/env python3
"""Integrate reader/adapter with copied AMD functions and modeled MMIO; LGPL-3.0-or-later."""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
from test_spd_vendor_receive import function
REPO=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bsp','patched-root','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    original=a.bsp/'libsrc/iicps/src';root=a.patched_root
    manifest=json.loads((root/'manifest.json').read_text())
    for name,entry in manifest['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=entry['output_sha256']:raise ValueError('Patched source changed: '+name)
        if hashlib.sha256((original/name).read_bytes()).hexdigest()!=entry['input_sha256']:raise ValueError('Original source changed: '+name)
    names={'xiicps_master.c':['XIicPs_MasterSend','XIicPs_MasterRecv','XIicPs_MasterInterruptHandler'],
           'xiicps_xfer.c':['XIicPs_SetupMaster','MasterSendData','XIicPs_MasterIntrSend','XIicPs_MasterIntrRead'],
           'xiicps_hw.c':['XIicPs_MasterRead'],
           'xiicps.c':['XIicPs_BusIsBusy','TransmitFifoFill'], 'xiicps_intr.c':['XIicPs_SetStatusHandler']}
    paths={n:(root/n if n in manifest['files'] else original/n) for n in names}
    bodies='\n'.join(function(paths[n].read_text(),fn) for n,functions in names.items() for fn in functions)
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);(d/'vendor_functions.inc').write_text(bodies);binary=d/'model'
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(a.bsp/'include'),'-I'+str(REPO/'diagnostics/ddr'),'-I'+str(d),str(REPO/'tests/spd_amd_register_model.c'),'-o',str(binary)],check=True)
        result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=5)
        if result.returncode:raise RuntimeError(result.stderr+result.stdout)
    files=[*paths.values(),REPO/'tests/spd_amd_register_model.c',REPO/'diagnostics/ddr/spd_reader.h',REPO/'diagnostics/ddr/spd_xiicps.h',REPO/'diagnostics/ddr/spd_xiicps_state.h',REPO/'diagnostics/ddr/spd_page.h',REPO/'diagnostics/ddr/spd_page_transfer.h',REPO/'diagnostics/ddr/spd_session.h']
    report=dict(status='READER_ADAPTER_PATCHED_AMD_REGISTER_MODEL_PASS',hardware_executed=False,hardware_admitted=False,functions=names,stdout=result.stdout,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},limits='Extracted functions with actual BSP macros and substituted MMIO; no physical bus timing/IRQ/page baseline/restoration/CRC proof.')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(result.stdout,end='')
if __name__=='__main__':main()
