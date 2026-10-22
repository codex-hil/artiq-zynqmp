#!/usr/bin/env python3
"""Emit isolated Piotr FSBL SPD UART instrumentation; LGPL-3.0-or-later."""
import argparse,difflib,hashlib,json
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
EXPECTED='ae48bfe6f1c478fd91bb16088d311ea5f8916e1ab43045184a614af868cd60a5'

def instrument(raw):
    if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise ValueError('Piotr DDR source changed: review before instrumentation')
    text=raw.decode()
    anchor='''\t/* ZCU102, ZCU106 and ZCU111, ZCU216, ZCU208 and ZCU670 Boards have'''
    if text.count(anchor)!=1:raise ValueError('Missing unique post-SPD success anchor')
    addition=r'''
    /* Diagnostic UART only: preserve Piotr/AMD SPD transactions and training. */
    XFsbl_Printf(DEBUG_GENERAL, "SPD_BASE_BEGIN bytes=128\r\n");
    for (u32 SpdDumpIndex = 0U; SpdDumpIndex < 128U; SpdDumpIndex++) {
        if ((SpdDumpIndex % 16U) == 0U) {
            XFsbl_Printf(DEBUG_GENERAL, "SPD_BASE %03u ", (unsigned int)SpdDumpIndex);
        }
        XFsbl_Printf(DEBUG_GENERAL, "%02x", (unsigned int)SpdData[SpdDumpIndex]);
        if ((SpdDumpIndex % 16U) == 15U) {
            XFsbl_Printf(DEBUG_GENERAL, "\r\n");
        }
    }
    XFsbl_Printf(DEBUG_GENERAL, "SPD_BASE_END\r\n");

'''
    return text.replace(anchor,addition+anchor).encode()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output file')
    src=REPO/'boards/genesys_zu-5ev/3_bootable/xfsbl_ddr_init.c';raw=src.read_bytes();result=instrument(raw)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    a.output.with_suffix('.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),result.decode().splitlines(True),fromfile='piotr/xfsbl_ddr_init.c',tofile='diagnostic/xfsbl_ddr_init.c')))
    a.output.with_suffix('.json').write_text(json.dumps({'status':'UART_ONLY_INSTRUMENTATION_SOURCE_PREPARED','source':str(src),'source_sha256':EXPECTED,'output_sha256':hashlib.sha256(result).hexdigest(),'extra_i2c_transactions':0,'hardware_executed':False},indent=2)+'\n')
if __name__=='__main__':main()
