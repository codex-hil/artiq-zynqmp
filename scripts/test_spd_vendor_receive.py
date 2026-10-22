#!/usr/bin/env python3
"""Execute extracted AMD receive ISR path against a host register model; LGPL-3.0-or-later."""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path

def function(source,name):
    import re
    match=re.search(r'^(?:void|s32) '+name+r'\([^;]*?\)\s*\{',source,re.M)
    if not match:raise ValueError('Missing vendor function '+name)
    start=match.start();pos=match.end();depth=1
    while depth:
        depth+=(source[pos]=='{')-(source[pos]=='}');pos+=1
    return source[start:pos]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bsp',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--patched-root',type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    root=a.patched_root or a.bsp/'libsrc/iicps/src';names={'xiicps_master.c':['XIicPs_MasterInterruptHandler'],'xiicps_xfer.c':['XIicPs_MasterIntrSend','XIicPs_MasterIntrRead'],'xiicps_hw.c':['XIicPs_MasterRead']}
    bodies='\n'.join(function((root/file).read_text(),n) for file,ns in names.items() for n in ns)
    model=r'''
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include "xiicps.h"
#include "xiicps_xfer.h"
#include "xplatform_info.h"
static jmp_buf guard;
static unsigned mode,reads;static u32 events,control,status;
static u32 model_read(UINTPTR base,u32 off) {
 (void)base;
 if(off==XIICPS_ISR_OFFSET)return status;
 if(off==XIICPS_IMR_OFFSET)return 0;
 if(off==XIICPS_CR_OFFSET)return control;
 if(off==XIICPS_SR_OFFSET)return mode==3 || mode==6 || reads<(mode==1?128U:mode==2?64U:0U)?XIICPS_SR_RXDV_MASK:0;
 return 0;
}
static void model_write(UINTPTR base,u32 off,u32 value) {(void)base;if(off==XIICPS_CR_OFFSET)control=value;}
static u32 model_data(UINTPTR address) {
 (void)address;
 /* Detect attempted out-of-buffer receive before vendor macro stores a byte. */
 if(reads>=128)longjmp(guard,1);
 return reads++;
}
#undef XIicPs_ReadReg
#undef XIicPs_WriteReg
#undef XIicPs_In32
#define XIicPs_ReadReg model_read
#define XIicPs_WriteReg model_write
#define XIicPs_In32 model_data
#define XIicPs_RxDataValid(p) (model_read((p)->Config.BaseAddress,XIICPS_SR_OFFSET)&XIICPS_SR_RXDV_MASK)
u32 XGetPlatform_Info(void) {return XPLAT_ZYNQ_ULTRA_MP;}
void MasterSendData(XIicPs *p) {(void)p;assert(!"Unexpected send path");}
void Xil_Assert(const char8 *file,s32 line) {(void)file;(void)line;assert(!"Vendor assertion");}
u32 Xil_AssertStatus;
static void callback(void *p,u32 value) {(void)p;events|=value;}
'''
    main=r'''
int main(void) {
 for(mode=0;mode<(EXPECT_BOUNDED?7U:6U);mode++) {
  XIicPs dev={0};u8 bytes[128]={0};reads=events=control=0;
  dev.IsReady=XIL_COMPONENT_IS_READY;dev.RecvBufferPtr=bytes;
  dev.RecvByteCount=mode==6?0:128;dev.CurrByteCount=mode==6?0:128;dev.StatusHandler=callback;
  status=mode==0?0:mode==4?XIICPS_IXR_NACK_MASK:mode==5?XIICPS_IXR_TO_MASK:(XIICPS_IXR_DATA_MASK|XIICPS_IXR_COMP_MASK);
  if(setjmp(guard)) {assert(!EXPECT_BOUNDED && mode==3 && reads==128);puts("STUCK_RXDV_OVERREAD_ATTEMPT_DETECTED");continue;}
  XIicPs_MasterInterruptHandler(&dev);
  if(mode==0)assert(reads==0 && dev.RecvByteCount==128 && !(events&XIICPS_EVENT_COMPLETE_RECV));
  if(mode==1)assert(reads==128 && dev.RecvByteCount==0 && events==XIICPS_EVENT_COMPLETE_RECV);
  if(mode==2)assert(reads==64 && dev.RecvByteCount==64 && !(events&XIICPS_EVENT_COMPLETE_RECV));
  if(mode==3)assert(EXPECT_BOUNDED && reads==128 && dev.RecvByteCount==0 && (events&XIICPS_EVENT_ERROR));
  if(mode==6)assert(EXPECT_BOUNDED && reads==0 && dev.RecvByteCount==0 && (events&XIICPS_EVENT_ERROR));
  if(mode==4)assert(reads==0 && (events&XIICPS_EVENT_NACK) && (events&XIICPS_EVENT_ERROR));
  if(mode==5)assert(reads==0 && (events&XIICPS_EVENT_TIME_OUT));
 }
 puts(EXPECT_BOUNDED?"PATCHED_VENDOR_ISR_BOUNDS_PASS":"VENDOR_ISR_MODEL_CONTROLS_PASS_KNOWN_STUCK_RXDV_DEFECT_RETAINED");
}
'''
    with tempfile.TemporaryDirectory() as d:
        c=Path(d)/'model.c';binary=Path(d)/'model';c.write_text('#define EXPECT_BOUNDED '+str(int(a.patched_root is not None))+'\n'+model+bodies+main)
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(a.bsp/'include'),str(c),'-o',str(binary)],check=True)
        r=subprocess.run([str(binary)],capture_output=True,text=True,timeout=5)
        if r.returncode:raise RuntimeError(r.stderr+r.stdout)
    result=dict(status='PATCHED_VENDOR_ISR_MODEL_BOUNDS_PASS' if a.patched_root else 'VENDOR_ISR_MODEL_PASS_WITH_KNOWN_OVERREAD_DEFECT',hardware_executed=False,hardware_admitted=False,stdout=r.stdout,source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [*(root/f for f in names),*(a.bsp/'include'/f for f in ['xiicps.h','xiicps_xfer.h','xiicps_hw.h'])]},functions=names,limits='Extracted vendor functions and actual BSP macros; host MMIO model only. Original or isolated patched sources selected explicitly. Not physical timing/full-driver/restoration proof.')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(r.stdout,end='')
if __name__=='__main__':main()
