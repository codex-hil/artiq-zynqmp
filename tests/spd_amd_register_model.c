/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "xiicps.h"
#include "xiicps_xfer.h"
#include "xplatform_info.h"
static u32 regs[64];static unsigned scenario,transactions,reads,tx_bytes,read_number;
static int receiving;
static u32 mmio_read(UINTPTR base,u32 off) {
 assert(base==0xff030000U && off/4<64);
 if(off==XIICPS_SR_OFFSET) {
  if(!receiving)return 0;
  if(scenario==3)return XIICPS_SR_RXDV_MASK; /* stuck FIFO indication */
  unsigned limit=scenario==2?64U:(scenario==1 || scenario==4 || scenario==5)?0U:128U;
  return reads<limit?XIICPS_SR_RXDV_MASK:0;
 }
 return regs[off/4];
}
static void mmio_write(UINTPTR base,u32 off,u32 value) {
 assert(base==0xff030000U && off/4<64);
 if(off==XIICPS_ISR_OFFSET) {regs[off/4]&=~value;return;}
 if(off==XIICPS_IER_OFFSET) {regs[XIICPS_IMR_OFFSET/4]&=~value;return;}
 if(off==XIICPS_IDR_OFFSET) {regs[XIICPS_IMR_OFFSET/4]|=value;return;}
 regs[off/4]=value;
 if(off==XIICPS_CR_OFFSET && (value&XIICPS_CR_CLR_FIFO_MASK)) {
  tx_bytes=0;regs[XIICPS_TRANS_SIZE_OFFSET/4]=0;
  regs[off/4]&=~XIICPS_CR_CLR_FIFO_MASK;
 }
 if(off==XIICPS_ADDR_OFFSET) {
  transactions++;receiving=(regs[XIICPS_CR_OFFSET/4]&XIICPS_CR_RD_WR_MASK)!=0;reads=0;
  if(receiving) {
   read_number++;assert(value==0x51 && regs[XIICPS_TRANS_SIZE_OFFSET/4]==128);
   regs[XIICPS_ISR_OFFSET/4]=scenario==1?XIICPS_IXR_NACK_MASK:scenario==4?0:
    scenario==5?XIICPS_IXR_TO_MASK:(XIICPS_IXR_DATA_MASK|XIICPS_IXR_COMP_MASK);
   if(scenario==6)regs[XIICPS_ISR_OFFSET/4]|=XIICPS_IXR_NACK_MASK;
  } else {
   assert((value==0x36 || value==0x51) && tx_bytes==1);
   regs[XIICPS_ISR_OFFSET/4]=XIICPS_IXR_COMP_MASK;
  }
 }
}
static u32 data_read(UINTPTR address) {
 assert(address==0xff030000U+XIICPS_DATA_OFFSET && reads<128);
 unsigned value=reads++;return value+(scenario==7 && read_number==2);
}
static void data_write(UINTPTR address,u32 value) {
 assert(address==0xff030000U+XIICPS_DATA_OFFSET && value==0);tx_bytes++;
}
#undef XIicPs_ReadReg
#undef XIicPs_WriteReg
#undef XIicPs_In32
#undef XIicPs_Out32
#define XIicPs_ReadReg mmio_read
#define XIicPs_WriteReg mmio_write
#define XIicPs_In32 data_read
#define XIicPs_Out32 data_write
#define XIicPs_RxDataValid(p) (mmio_read((p)->Config.BaseAddress,XIICPS_SR_OFFSET)&XIICPS_SR_RXDV_MASK)
u32 XGetPlatform_Info(void) {return XPLAT_ZYNQ_ULTRA_MP;}
void Xil_Assert(const char8 *file,s32 line) {(void)file;(void)line;assert(!"Vendor assertion");}
u32 Xil_AssertStatus;
#include "spd_xiicps.h"
#include "vendor_functions.inc"
int main(void) {
 for(scenario=0;scenario<8;scenario++) {
  XIicPs dev={0};struct spd_xiicps a;struct spd_transport t;struct spd_reader r;
  memset(regs,0,sizeof(regs));transactions=reads=tx_bytes=read_number=0;receiving=0;
  dev.Config.BaseAddress=0xff030000U;dev.IsReady=XIL_COMPONENT_IS_READY;
  assert(spd_amd_bind(&a,&dev,1,&t)==0);
  spd_reader_init(&r,t,0,1);
  for(unsigned i=1;i<40000 && !r.stopped;i++)spd_reader_tick(&r,i*10U);
  assert(r.stopped);
  if(scenario==0)assert(r.result==SPD_PASS && r.page_restored && transactions==6 && !a.poisoned);
  else if(scenario==7)assert(r.result==SPD_MISMATCH && r.page_restored && transactions==6);
  else {
   assert(r.result!=SPD_PASS && !r.page_restored && transactions==3);
   if(scenario==2 || scenario==4)assert(r.result==SPD_DEADLINE && a.active);
   else assert(r.result==SPD_IO_ERROR && a.poisoned);
   uint8_t zero=0;
   assert(t.begin(t.ctx,SPD_LOWER_PAGE,0x36,&zero,1)==-1 && transactions==3);
  }
 }
 puts("ADAPTER_READER_ACTUAL_AMD_MMIO_MODEL_8_SCENARIOS_PASS");
}
