/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "xiicps.h"
#include "xiicps_xfer.h"
#include "xplatform_info.h"
static u32 regs[64];static unsigned scenario,transactions,reads,tx_bytes,read_number;
static int receiving;
static int page_query,query_page;
static unsigned transfer_limit;
static u32 query_events;
static void query_callback(void *ref,u32 events) {(void)ref;query_events|=events;}
static unsigned writes;
static void original_callback(void *ref,u32 events) {(void)ref;(void)events;assert(!"Old callback during diagnostic");}
static int corrupt_restore;
static u32 mmio_read(UINTPTR base,u32 off) {
 assert(base==0xff030000U && off/4<64);
 if(off==XIICPS_SR_OFFSET) {
  if(!receiving)return 0;
  if(page_query)return !query_page && reads<1?XIICPS_SR_RXDV_MASK:0;
  if(scenario==3)return XIICPS_SR_RXDV_MASK; /* stuck FIFO indication */
  unsigned limit=scenario==2?64U:(scenario==1 || scenario==4 || scenario==5)?0U:128U;
  return reads<limit?XIICPS_SR_RXDV_MASK:0;
 }
 return regs[off/4];
}
static void mmio_write(UINTPTR base,u32 off,u32 value) {
 assert(base==0xff030000U && off/4<64);
 writes++;
 if(corrupt_restore && off==XIICPS_TIME_OUT_OFFSET)return;
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
   read_number++;transfer_limit=regs[XIICPS_TRANS_SIZE_OFFSET/4];
   if(page_query) {
    assert(value==0x36 && transfer_limit==1);
    regs[XIICPS_ISR_OFFSET/4]=query_page?XIICPS_IXR_NACK_MASK:XIICPS_IXR_COMP_MASK;
    return;
   }
   assert(value==0x51 && transfer_limit==128);
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
 unsigned value=reads++;regs[XIICPS_TRANS_SIZE_OFFSET/4]=transfer_limit-reads;return value+(scenario==7 && read_number==2);
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
#include "spd_xiicps_state.h"
#include "spd_page.h"
#include "vendor_functions.inc"
int main(void) {
 for(scenario=0;scenario<8;scenario++) {
  XIicPs dev={0};struct spd_xiicps a;struct spd_transport t;struct spd_reader r;struct spd_amd_snapshot saved;
  memset(regs,0,sizeof(regs));transactions=reads=tx_bytes=read_number=0;receiving=0;
  dev.Config.BaseAddress=0xff030000U;dev.IsReady=XIL_COMPONENT_IS_READY;
  dev.StatusHandler=original_callback;dev.CallBackRef=&dev;
  regs[XIICPS_TIME_OUT_OFFSET/4]=17;
  assert(spd_amd_snapshot(&saved,&dev,1)==0);
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
  if(scenario==0 || scenario==7) {
   regs[XIICPS_TIME_OUT_OFFSET/4]=99;
   assert(spd_amd_restore(&saved,&a,1)==0);
   assert(regs[XIICPS_TIME_OUT_OFFSET/4]==17 && dev.StatusHandler==original_callback && dev.CallBackRef==&dev);
   assert(a.dev==NULL && !saved.valid);
   assert(spd_amd_restore(&saved,&a,1)==-1);
  } else {
   unsigned before=writes;
   assert(spd_amd_restore(&saved,&a,1)==-1 && writes==before);
  }
 }
 /* Snapshot refusal is read-only; restoration verifies register readback. */
 {
  XIicPs dev={0};struct spd_xiicps a;struct spd_transport t;struct spd_amd_snapshot saved;
  memset(regs,0,sizeof(regs));receiving=0;scenario=0;
  dev.Config.BaseAddress=0xff030000U;dev.IsReady=XIL_COMPONENT_IS_READY;
  for(unsigned fault=0;fault<7;fault++) {
   memset(regs,0,sizeof(regs));dev.SendByteCount=dev.RecvByteCount=0;
   if(fault==4)dev.SendByteCount=1;
   if(fault==5)dev.RecvByteCount=1;
   if(fault==6)regs[XIICPS_CR_OFFSET/4]=XIICPS_CR_CLR_FIFO_MASK;
   if(fault==1)regs[XIICPS_ISR_OFFSET/4]=XIICPS_IXR_COMP_MASK;
   if(fault==2)regs[XIICPS_TRANS_SIZE_OFFSET/4]=1;
   if(fault==3)regs[XIICPS_CR_OFFSET/4]=XIICPS_CR_HOLD_MASK;
   unsigned before=writes;
   assert(spd_amd_snapshot(&saved,&dev,fault!=0)==-1 && writes==before);
  }
  memset(regs,0,sizeof(regs));regs[XIICPS_TIME_OUT_OFFSET/4]=17;
  assert(spd_amd_snapshot(&saved,&dev,1)==0);
  assert(spd_amd_bind(&a,&dev,1,&t)==0);
  regs[XIICPS_TIME_OUT_OFFSET/4]=99;corrupt_restore=1;
  assert(spd_amd_restore(&saved,&a,1)==-1 && a.poisoned && !saved.valid);
 }
 /* Dedicated page query only; does not change generic adapter NACK policy. */
 page_query=1;corrupt_restore=0;
 for(query_page=0;query_page<2;query_page++) {
  XIicPs dev={0};u8 byte=0;memset(regs,0,sizeof(regs));reads=query_events=0;
  dev.Config.BaseAddress=0xff030000U;dev.IsReady=XIL_COMPONENT_IS_READY;
  XIicPs_SetStatusHandler(&dev,NULL,query_callback);
  XIicPs_MasterRecv(&dev,&byte,1,0x36);
  u32 raw=regs[XIICPS_ISR_OFFSET/4];
  XIicPs_MasterInterruptHandler(&dev);
  struct spd_page_reply reply={.address=0x36,.requested=1,.received=1-dev.RecvByteCount,
   .raw_irq=raw,.events=query_events,.exclusive_route_proven=1,
   .independent_spd_identity_proven=1,.bus_idle=1,.fifo_empty=(mmio_read(0xff030000U,XIICPS_SR_OFFSET)&XIICPS_SR_RXDV_MASK)==0};
  assert((int)spd_classify_page(reply)==query_page);
  assert(spd_page_restore_confirmed((enum spd_page)query_page,reply));
  reply.independent_spd_identity_proven=0;
  assert(spd_classify_page(reply)==SPD_PAGE_UNKNOWN);
 }
 puts("ADAPTER_READER_AMD_MODEL_AND_PAGE_QUERY_CLASSIFICATION_PASS");
}
