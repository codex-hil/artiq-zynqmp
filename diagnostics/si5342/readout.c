/* Read-only Si5342 diagnostic. Only I2C mux/page-pointer writes occur.
 * Uses maintained AMD XIicPs; does not write frequency, reset or OTP registers.
 */
#include "xiicps.h"
#include "xil_printf.h"
#include "sleep.h"
#include "xstatus.h"
static XIicPs bus;

static int send(unsigned addr, u8 *data, unsigned n) {
 int r=XIicPs_MasterSendPolled(&bus,data,n,addr);
 if(r!=XST_SUCCESS) {xil_printf("I2C_SEND_ERROR %02x %d\r\n",addr,r);return -1;}
 return 0;
}
static int recv(unsigned addr,u8 *data,unsigned n) {
 int r=XIicPs_MasterRecvPolled(&bus,data,n,addr);
 if(r!=XST_SUCCESS) {xil_printf("I2C_RECV_ERROR %02x %d\r\n",addr,r);return -1;}
 return 0;
}
static void releasebus(void) {
 XIicPs_ClearOptions(&bus,XIICPS_REP_START_OPTION);
 XIicPs_WriteReg(bus.Config.BaseAddress,XIICPS_CR_OFFSET,
   XIicPs_ReadReg(bus.Config.BaseAddress,XIICPS_CR_OFFSET)&~XIICPS_CR_HOLD_MASK);
}
static int beginchannel(void) {
 for(unsigned retry=0;retry<8;retry++) {
  u8 selected=0,wanted=4;
  for(unsigned wait=0; XIicPs_BusIsBusy(&bus) && wait<10000;wait++)usleep(1);
  XIicPs_SetOptions(&bus,XIICPS_REP_START_OPTION);
  if(recv(0x70,&selected,1)) {releasebus();return -1;}
  if(selected==wanted) {usleep(100);return 0;}
  xil_printf("MUX_RETRY %02x\r\n",selected);
  XIicPs_ClearOptions(&bus,XIICPS_REP_START_OPTION);
  if(send(0x70,&wanted,1)) {releasebus();return -1;}
 }
 return -1;
}
static int readreg(unsigned reg,u8 *value) {
 u8 p[2]={1,reg>>8},a=reg;
 if(beginchannel())return -1;
 /* Page write ends with STOP; reacquire/check mux afterward.
  * Keep the register-pointer/data pair under repeated START. The 100us
  * RX-to-TX settling guard was necessary in physical XIicPs trials.
  */
 XIicPs_ClearOptions(&bus,XIICPS_REP_START_OPTION);
 if(send(0x68,p,2)) {releasebus();return -1;}
 if(beginchannel())return -1;
 if(send(0x68,&a,1)) {releasebus();return -1;}
 usleep(100);
 XIicPs_ClearOptions(&bus,XIICPS_REP_START_OPTION);
 if(recv(0x68,value,1)) {releasebus();return -1;}
 return 0;
}
static void restore_mux(u8 saved) {
 u8 selected;
 XIicPs_SetOptions(&bus,XIICPS_REP_START_OPTION);
 if(recv(0x70,&selected,1)) {releasebus();return;}
 XIicPs_ClearOptions(&bus,XIICPS_REP_START_OPTION);
 send(0x70,&saved,1);
}
int main(void) {
 xil_printf("SI5342_READONLY_BEGIN\r\n");
 for(unsigned controller=0;controller<2;controller++) {
  unsigned base=0xff020000+controller*0x10000;
  XIicPs_Config *cfg=XIicPs_LookupConfig(base);
  if(!cfg||XIicPs_CfgInitialize(&bus,cfg,base)!=XST_SUCCESS||XIicPs_SetSClk(&bus,100000)!=XST_SUCCESS) {xil_printf("I2C_INIT_FAIL %08x\r\n",base);continue;}
  u8 saved=0;
  xil_printf("I2C_BUS %08x\r\n",base);
  if(recv(0x70,&saved,1))continue;
  xil_printf("MUX_BASELINE 70 %02x\r\n",saved);
  u8 lo=0,hi=0,rev=0;
  if(readreg(2,&lo)||readreg(3,&hi)||readreg(5,&rev)) {restore_mux(saved);continue;}
  xil_printf("SI_ID %02x%02x REV %02x\r\n",hi,lo,rev);
  if(lo!=0x42||hi!=0x53) {restore_mux(saved);continue;}
  int failed=0;
  for(unsigned reg=0;reg<0xC00;reg++) {
   u8 value=0;
   if(readreg(reg,&value)) {xil_printf("REG_FAIL %04x\r\n",reg);failed=1;break;}
   if((reg&255)==1 && value!=(reg>>8)) {xil_printf("PAGE_VERIFY_FAIL %04x %02x\r\n",reg,value);failed=1;break;}
   xil_printf("REG %04x %02x\r\n",reg,value);
  }
  restore_mux(saved);
  xil_printf("SI5342_READONLY_END %s\r\n",failed?"FAIL":"PASS");
  while(1)usleep(1000000);
 }
 xil_printf("SI5342_READONLY_END NOT_FOUND\r\n");
 while(1)usleep(1000000);
 return 0;
}
