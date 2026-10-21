/* A53 lab AUX request/reply with upstream Rust codec, LGPL-3.0-or-later.
 * Both roles share one CPU and real GTH PMA loopback; not remote discovery. */
#include <stdint.h>
#include <string.h>
#include "xil_cache.h"
#include "xil_printf.h"
#include "sleep.h"
#include "bspconfig.h"
#include "xuartps_hw.h"
#include "aux_regs.h"
#ifdef AUX_TSC
#include "tsc_ack_policy.h"
#endif
extern int32_t aux_encode(uint32_t,uint32_t,uint8_t*,uintptr_t);
extern int32_t aux_decode(const uint8_t*,uintptr_t,uint32_t*);
extern uint32_t aux_crc(const uint8_t*,uintptr_t);
static uint32_t received[256];
static uint32_t rd(uintptr_t a) { __asm__ volatile("dsb sy":::"memory");return *(volatile uint32_t*)a; }
static void wr(uintptr_t a,uint32_t v) { *(volatile uint32_t*)a=v;__asm__ volatile("dsb sy":::"memory"); }
void aux_panic(void) { xil_printf("AUX_FW PANIC\r\n");while(1)usleep(1000000); }
static int wait(uintptr_t a,uint32_t value) {
 for(unsigned i=0;i<10000;i++) {if(rd(a)==value)return 0;usleep(1000);}return -1;
}
#ifdef AUX_RESET
#include "reset_backend.h"
#ifdef AUX_DIO
#include "leaf_policy.h"
#endif
#endif
#ifdef AUX_SNAPSHOT
#include "tsc_a53.h"
static int snapshot_ready(void *context) {
 (void)context;
 return reset_backend_ready() && !rd(REG_AUX_RTIO_RESET_REQUEST) &&
  !rd(REG_AUX_RTIO_RESET_APPLIED) && !rd(REG_AUX_RTIO_ERROR_FLAGS);
}
static void snapshot_probe(void) {
 struct tsc_reader reader=tsc_a53_bind(0,snapshot_ready);
 uint64_t previous=0;
 for(unsigned i=0;i<4;i++) {
  uint64_t upper;
  if(tsc_read_upper(&reader,&upper))goto bad;
  uint64_t sample=((uint64_t)rd(REG_AUX_TSC_SNAPSHOT_VALUE)<<32)|rd(REG_AUX_TSC_SNAPSHOT_VALUE+4);
  if((i && sample<=previous) || (sample&7) || upper<sample)goto bad;
  previous=sample;
  xil_printf("AUX_SNAPSHOT SAMPLE index=%u hi=%08x lo=%08x allowance=%u\r\n",
   i,(uint32_t)(sample>>32),(uint32_t)sample,(uint32_t)(upper-sample));
  usleep(100);
 }
 xil_printf("AUX_SNAPSHOT PASS reads=4\r\n");return;
bad:
 xil_printf("AUX_SNAPSHOT FAIL\r\n");wr(REG_MONITOR_TX_ENABLE,0);aux_panic();
}
#endif
static int send(const uint8_t *data,unsigned length) {
 if(!length || length%4 || length>1024 || wait(REG_AUX_AUX_TX,0) || wait(REG_AUX_BRIDGE_BUSY,0))return -1;
 for(unsigned i=0;i<length/4;i++) {uint32_t word;memcpy(&word,data+4*i,4);wr(AUX_MEMORY+4*i,word);}
 wr(REG_AUX_AUX_TX_LENGTH,length);wr(REG_AUX_AUX_TX,1);
 return wait(REG_AUX_AUX_TX,0)||wait(REG_AUX_BRIDGE_BUSY,0)?-1:0;
}
#ifdef AUX_DDMA
#include "ddma_lab_admission.h"
#define ddma_backend_start ddma_lab_admission_start
#include "ddma_runtime.h"
#undef ddma_backend_start
#include "ddma_lab_runtime.h"
static struct ddma_packet ddma_received;
#endif
static int receive(uint32_t *destination) {
 if(wait(REG_AUX_AUX_RX_PRESENT,1) || rd(REG_AUX_AUX_RX_ERROR))return -99;
 unsigned pointer=rd(REG_AUX_AUX_READ_POINTER);
 for(unsigned i=0;i<256;i++)received[i]=rd(AUX_MEMORY+8192+1024*pointer+4*i);
 int kind;
#ifdef AUX_DDMA
 if(((uint8_t*)received)[0]>=0xb0 && ((uint8_t*)received)[0]<=0xb6)
  kind=aux_ddma_decode((uint8_t*)received,sizeof(received),&ddma_received);
 else
#endif
 kind=aux_decode((uint8_t*)received,sizeof(received),destination);
 wr(REG_AUX_AUX_RX_PRESENT,1);
 return kind;
}
static int exchange(unsigned request,unsigned destination,unsigned reply) {
 uint8_t bytes[16];uint32_t d=0;
 int size=aux_encode(request,destination,bytes,sizeof(bytes));
 if(size<0 || send(bytes,size) || receive(&d)!=(int)request)return -1;
 if(request==0x20 && d!=destination)return -1;
 /* No RTIO backend: destination is explicitly reported DOWN. ResetAck
  * acknowledges a laboratory AUX handler; it is not a production RTIO reset. */
 size=aux_encode(reply,0,bytes,sizeof(bytes));
 if(size<0 || send(bytes,size) || receive(&d)!=(int)reply)return -1;
 xil_printf("AUX_FW EXCHANGE request=%u reply=%u PASS\r\n",request,reply);
 return 0;
}
/* Persistent responder; optional reset ACK requires hardware completion. */
static void service(void) {
#ifdef AUX_TSC
 struct tsc_ack_state tsc_state={0,0};
#ifdef AUX_DIO
 unsigned rank=0;uint8_t local_route[256]={0};
#endif
#endif
#ifdef AUX_DDMA
 ddma_init();
#endif
 xil_printf("AUX_SERVICE READY\r\n");
 while(1) {
#ifdef AUX_DDMA
  ddma_poll();
  ddma_lab_poll();
  if(XUartPs_IsReceiveData(STDIN_BASEADDRESS)) {
   unsigned command=XUartPs_ReadReg(STDIN_BASEADDRESS,XUARTPS_FIFO_OFFSET)&255;
   if(command=='F')ddma_lab_request();
   if(command=='I')ddma_lab_idle();
  }
#endif
  unsigned in_reset=rd(REG_AUX_IN_RESET),ready=rd(REG_AUX_RX_UP);
  if(in_reset || !ready) {
#ifdef AUX_TSC
   tsc_ack_step(&tsc_state,0,in_reset,ready,0);
#endif
   usleep(1000);continue;
  }
#ifdef AUX_TSC
  uint32_t loads=rd(REG_AUX_TSC_LOAD_COUNT);
  unsigned faults=rd(REG_AUX_RT_REPLY_FAULT)|rd(REG_AUX_RTIO_ERROR_FLAGS);
  int action=tsc_ack_step(&tsc_state,loads,0,1,faults!=0);
  if(action<0)xil_printf("AUX_TSC REJECT count=%u fault=%u\r\n",loads,faults);
  if(action>0) {
   uint8_t bytes[16];int size=aux_encode(4,0,bytes,sizeof(bytes));
   if(size<0||send(bytes,size)) {wr(REG_MONITOR_TX_ENABLE,0);aux_panic();}
   xil_printf("AUX_TSC ACK count=%u\r\n",loads);
#ifdef AUX_SNAPSHOT
   snapshot_probe();
#endif
  }
#endif
#ifndef AUX_EXTERNAL
  if(XUartPs_IsReceiveData(STDIN_BASEADDRESS)) {
   unsigned command=XUartPs_ReadReg(STDIN_BASEADDRESS,XUARTPS_FIFO_OFFSET)&255;
   uint8_t bytes[16];int size=-1;
   if(command=='e'||command=='c'||command=='u')size=aux_encode(0,0,bytes,sizeof(bytes));
   if(command=='d')size=aux_encode(0x20,1,bytes,sizeof(bytes));
   if(command=='r')size=aux_encode(2,0,bytes,sizeof(bytes));
   if(size>0) {
    if(command=='c')bytes[size-1]^=0x80;
    if(command=='u') {bytes[0]=0xff;uint32_t crc=aux_crc(bytes,4);memcpy(bytes+4,&crc,4);}
    if(send(bytes,size))xil_printf("AUX_SERVICE SEND_FAIL\r\n");
   }
  }
#endif
  if(rd(REG_AUX_AUX_RX_ERROR)) {
   xil_printf("AUX_SERVICE RX_ERROR\r\n");wr(REG_AUX_AUX_RX_ERROR,1);
  }
  if(rd(REG_AUX_AUX_RX_PRESENT)) {
   uint32_t destination=0;int request=receive(&destination);
#ifdef AUX_DDMA
   if(request>=0xb0 && request<=0xb6) {
    unsigned leaf=leaf_ready(1,rank,local_route[1],tsc_state.seen,tsc_state.blocked,
      reset_backend_ready(),rd(REG_AUX_RTIO_RESET_REQUEST)|rd(REG_AUX_RTIO_RESET_APPLIED),
      rd(REG_AUX_RTIO_ERROR_FLAGS));
    if(!ddma_handle(request,&ddma_received,leaf))xil_printf("AUX_DDMA DROP kind=%u\r\n",request);
    continue;
   }
   if(request==2 && (ddma.running || ddma.status_pending))ddma_fatal();
#endif
   int reply=request==0?1:request==0x20?0x21:-1;
#ifdef AUX_DIO
   if(request==0x30) {
    local_route[destination&255]=(destination>>8)&1;
    reply=0x32;
   }
   if(request==0x31 && destination==1) {rank=1;reply=0x32;}
   if(request==0x20 && leaf_ready(destination,rank,local_route[1],
      tsc_state.seen,tsc_state.blocked,reset_backend_ready(),
      rd(REG_AUX_RTIO_RESET_REQUEST)|rd(REG_AUX_RTIO_RESET_APPLIED),
      rd(REG_AUX_RTIO_ERROR_FLAGS)))reply=0x22;
#endif
#ifdef AUX_RESET
   if(request==2) {
    if(reset_backend()) {
     xil_printf("AUX_RESET REJECT\r\n");
     wr(REG_MONITOR_TX_ENABLE,0);aux_panic();
    }
    xil_printf("AUX_RESET COMPLETE count=%u\r\n",rd(REG_AUX_TSC_LOAD_COUNT));
    reply=3;
   }
#endif
   if(reply>=0) {
    uint8_t bytes[16];int size=aux_encode(reply,0,bytes,sizeof(bytes));
    if(size<0||send(bytes,size)) {
     xil_printf("AUX_SERVICE SEND_FAIL\r\n");
#ifdef AUX_RESET
     wr(REG_MONITOR_TX_ENABLE,0);aux_panic();
#endif
    }
    else xil_printf("AUX_SERVICE RESPOND request=%d reply=%d\r\n",request,reply);
   } else if(request==1||request==3||request==0x21) {
    /* Local loopback sees our response: do not answer a response. */
    xil_printf("AUX_SERVICE IGNORE reply=%d\r\n",request);
   } else xil_printf("AUX_SERVICE DROP kind=%d\r\n",request);
  }
  usleep(100);
 }
}
int main(void) {
 Xil_DCacheDisable();
#ifdef AUX_EXTERNAL
 #ifdef AUX_RESET
 xil_printf("AUX_EXTERNAL START upstream-codec split-reset RTIO-backend\r\n");
#else
 xil_printf("AUX_EXTERNAL START upstream-codec\r\n");
#endif
 if(rd(REG_MONITOR_MAGIC)!=0x44525430)goto fail;
 wr(REG_MONITOR_TX_ENABLE,0);wr(REG_MONITOR_RESET,1);
 wr(REG_MONITOR_PRBS,0);wr(REG_MONITOR_TX_PRBS,0);wr(REG_MONITOR_LOOPBACK,0);
 usleep(50000);wr(REG_MONITOR_RESET,0);
 if(wait(REG_AUX_IN_RESET,0) || wait(REG_AUX_RX_UP,1))goto fail;
 usleep(25000);
#ifdef AUX_RESET
 if(release_backend()) {
  xil_printf("AUX_RESET COLD_RELEASE FAIL rtio_request=%u rtio_applied=%u phy_request=%u phy_applied=%u loads=%u\r\n",
   rd(REG_AUX_RTIO_RESET_REQUEST),rd(REG_AUX_RTIO_RESET_APPLIED),
   rd(REG_AUX_PHY_RESET_REQUEST),rd(REG_AUX_PHY_RESET_APPLIED),rd(REG_AUX_TSC_LOAD_COUNT));
  goto fail;
 }
 xil_printf("AUX_RESET COLD_RELEASE PASS\r\n");
#endif
#ifdef AUX_TSC
 if(rd(REG_AUX_TSC_LOAD_COUNT)!=0)goto fail;
 xil_printf("AUX_TSC BASELINE count=0\r\n");
#endif
 wr(REG_MONITOR_TX_ENABLE,1);
 #ifdef AUX_DIO
 xil_printf("AUX_EXTERNAL TX_IDLE_ENABLED single-hop-leaf destination=1\r\n");
#else
 xil_printf("AUX_EXTERNAL TX_IDLE_ENABLED destination=DOWN\r\n");
#endif
 service();
#else
 xil_printf("AUX_FW START upstream-codec\r\n");
 if(rd(REG_MONITOR_MAGIC)!=0x44525430)goto fail;
 wr(REG_MONITOR_TX_ENABLE,0);wr(REG_MONITOR_RESET,1);
 wr(REG_MONITOR_PRBS,0);wr(REG_MONITOR_TX_PRBS,0);wr(REG_MONITOR_LOOPBACK,2);
 usleep(50000);wr(REG_MONITOR_RESET,0);
 if(wait(REG_AUX_IN_RESET,0) || wait(REG_AUX_RX_UP,1))goto fail;
 usleep(25000);
 for(unsigned cycle=0;cycle<10;cycle++)
  if(exchange(0,0,1)||exchange(2,0,3)||exchange(0x20,1,0x21))goto fail;
 {
  uint8_t bytes[16];uint32_t destination=0;
  int size=aux_encode(0,0,bytes,sizeof(bytes));
  bytes[size-1]^=0x80;
  if(send(bytes,size)||receive(&destination)!=-1)goto fail;
  xil_printf("AUX_FW BAD_CRC PASS\r\n");
  size=aux_encode(0,0,bytes,sizeof(bytes));bytes[0]=0xff;
  uint32_t checksum=aux_crc(bytes,4);memcpy(bytes+4,&checksum,4);
  if(send(bytes,size)||receive(&destination)!=-2)goto fail;
  xil_printf("AUX_FW UNKNOWN_TYPE PASS\r\n");
 }
 if(exchange(0,0,1)||rd(REG_AUX_AUX_RX_ERROR)||rd(REG_AUX_AUX_RX_PRESENT))goto fail;
 xil_printf("TEST ARTIQ_AUX_FIRMWARE PASS\r\n");
 service();
#endif
fail:
 wr(REG_MONITOR_TX_ENABLE,0);
 xil_printf("TEST ARTIQ_AUX_FIRMWARE FAIL\r\n");
 while(1)usleep(1000000);
 return 1;
}
