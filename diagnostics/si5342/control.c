/* Temporary UART register service; volatile writes only, OTP inaccessible.
 * Same XIicPs/mux transport as the read-only backup utility. */
#define main backup_main
#include "readout.c"
#undef main
#include "bspconfig.h"
#include "xuartps_hw.h"
static int allowed(unsigned r) {
 return r==0x28a || r==0x28e || r==0x1e || r==0x1c || r==0x2c || (r>=0x2d&&r<=0x69) ||
 (r>=0x92&&r<=0xa0) || (r>=0xa9&&r<=0xac) || r==0xe5 ||
 (r>=0xea&&r<=0xed) || (r>=0x294&&r<=0x2ab) || r==0x804 || r==0xb44 || r==0xb47 || r==0xb48 ||
 (r>=0x208&&r<=0x234) || (r>=0x508&&r<=0x5a6) ||
 r==0x540 || r==0x949 || r==0x94a || r==0xb24 || r==0xb25;
}
static int writereg(unsigned reg,u8 value) {
 u8 page[2]={1,reg>>8},data[2]={reg,value};
 if(!allowed(reg))return -2;
 if(beginchannel())return -1;
 XIicPs_ClearOptions(&bus,XIICPS_REP_START_OPTION);
 if(send(0x68,page,2)) {releasebus();return -1;}
 if(beginchannel())return -1;
 XIicPs_ClearOptions(&bus,XIICPS_REP_START_OPTION);
 if(send(0x68,data,2)) {releasebus();return -1;}
 for(unsigned i=0;XIicPs_BusIsBusy(&bus)&&i<10000;i++)usleep(1);
 return XIicPs_BusIsBusy(&bus)?-1:0;
}
static int digit(char c) {
 if(c>='0'&&c<='9')return c-'0';
 if(c>='a'&&c<='f')return c-'a'+10;
 if(c>='A'&&c<='F')return c-'A'+10;
 return -1;
}
int main(void) {
 unsigned base=0xff020000;
 XIicPs_Config *cfg=XIicPs_LookupConfig(base);
 if(!cfg||XIicPs_CfgInitialize(&bus,cfg,base)!=XST_SUCCESS||XIicPs_SetSClk(&bus,100000)!=XST_SUCCESS)return 1;
 u8 lo,hi;
 if(readreg(2,&lo)||readreg(3,&hi)||lo!=0x42||hi!=0x53) {xil_printf("SI_CONTROL_FAIL\r\n");return 1;}
 xil_printf("SI_CONTROL_READY 5342\r\n");
 char line[16]; unsigned n=0;
 while(1) {
  char c=XUartPs_RecvByte(STDIN_BASEADDRESS);
  if(c=='\r')continue;
  if(c!='\n') {if(n<sizeof(line)-1)line[n++]=c;continue;}
  unsigned reg=0,val=0; int valid=1;
  for(unsigned i=1;i<n;i++) {int d=digit(line[i]);if(d<0){valid=0;break;} if(i<=4)reg=(reg<<4)|d;else val=(val<<4)|d;}
  if(!valid) xil_printf("ERR FORMAT\r\n");
  else if(n==5&&line[0]=='R') {
   u8 value=0;if(readreg(reg,&value))xil_printf("ERR READ\r\n");
   else xil_printf("READ %04x %02x\r\n",reg,value);
  } else if(n==7&&line[0]=='W') {
   int r=writereg(reg,val);xil_printf("WRITE %04x %02x %d\r\n",reg,val,r);
  } else xil_printf("ERR COMMAND\r\n");
  n=0;
 }
}
