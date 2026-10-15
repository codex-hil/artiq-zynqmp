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
static int send(const uint8_t *data,unsigned length) {
 if(!length || length%4 || length>1024 || wait(REG_AUX_AUX_TX,0) || wait(REG_AUX_BRIDGE_BUSY,0))return -1;
 for(unsigned i=0;i<length/4;i++) {uint32_t word;memcpy(&word,data+4*i,4);wr(AUX_MEMORY+4*i,word);}
 wr(REG_AUX_AUX_TX_LENGTH,length);wr(REG_AUX_AUX_TX,1);
 return wait(REG_AUX_AUX_TX,0)||wait(REG_AUX_BRIDGE_BUSY,0)?-1:0;
}
static int receive(uint32_t *destination) {
 if(wait(REG_AUX_AUX_RX_PRESENT,1) || rd(REG_AUX_AUX_RX_ERROR))return -99;
 unsigned pointer=rd(REG_AUX_AUX_READ_POINTER);
 for(unsigned i=0;i<256;i++)received[i]=rd(AUX_MEMORY+8192+1024*pointer+4*i);
 int kind=aux_decode((uint8_t*)received,sizeof(received),destination);
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
/* Persistent minimal responder. Reset has no production backend yet and
 * must not receive a successful acknowledgement from this service. */
static void service(void) {
 xil_printf("AUX_SERVICE READY\r\n");
 while(1) {
  if(rd(REG_AUX_IN_RESET) || !rd(REG_AUX_RX_UP)) {usleep(1000);continue;}
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
   int reply=request==0?1:request==0x20?0x21:-1;
   if(reply>=0) {
    uint8_t bytes[16];int size=aux_encode(reply,0,bytes,sizeof(bytes));
    if(size<0||send(bytes,size))xil_printf("AUX_SERVICE SEND_FAIL\r\n");
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
 xil_printf("AUX_EXTERNAL START upstream-codec no-RTIO-backend\r\n");
 if(rd(REG_MONITOR_MAGIC)!=0x44525430)goto fail;
 wr(REG_MONITOR_TX_ENABLE,0);wr(REG_MONITOR_RESET,1);
 wr(REG_MONITOR_PRBS,0);wr(REG_MONITOR_TX_PRBS,0);wr(REG_MONITOR_LOOPBACK,0);
 usleep(50000);wr(REG_MONITOR_RESET,0);
 if(wait(REG_AUX_IN_RESET,0) || wait(REG_AUX_RX_UP,1))goto fail;
 usleep(25000);
 wr(REG_MONITOR_TX_ENABLE,1);
 xil_printf("AUX_EXTERNAL TX_IDLE_ENABLED destination=DOWN\r\n");
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
