/* Autonomous laboratory clock manager using the validated AMD XIicPs transport.
 * LGPL-3.0-or-later. Not a production DRTIO clock/RTIO synchronization service. */
#define SI_NO_MAIN
#include "control.c"
#include "profile_rx125.h"
#include <stdint.h>

#define NPROFILE (sizeof(clock_profile)/sizeof(clock_profile[0]))
static u8 saved[NPROFILE], saved_control[3];
static int changed;
static void csr_write(unsigned offset,u32 value) {
 *(volatile u32 *)(uintptr_t)(0xa0000000u+offset)=value;
 __asm__ volatile("dsb sy" ::: "memory");
}
static u32 csr_read(unsigned offset) {
 __asm__ volatile("dsb sy" ::: "memory");
 return *(volatile u32 *)(uintptr_t)(0xa0000000u+offset);
}
static int checked(unsigned reg,u8 value) {
 u8 actual;
 if(writereg(reg,value)||readreg(reg,&actual)||actual!=value) {
  xil_printf("CLOCK WRITE_FAIL %04x\r\n",reg);return -1;
 }
 return 0;
}
static int preamble(void) {
 if(checked(0xb24,0xc0)||checked(0xb25,0)||checked(0x540,1))return -1;
 usleep(300000);return 0;
}
static int finish(void) {
 if(writereg(0x514,1)||writereg(0x1c,1))return -1;
 usleep(50000);
 return checked(0x540,0)||checked(0xb24,0xc3)||checked(0xb25,2)?-1:0;
}
static int locked(void) {
 u8 internal,inputs,pll,cal,active;
 if(readreg(0xc,&internal)||readreg(0xd,&inputs)||readreg(0xe,&pll)||
    readreg(0xf,&cal)||readreg(0x507,&active))return -1;
 return !(pll&0x22)&&!(inputs&0x11)&&!(internal&0x0b)&&!(cal&0x20)&&!(active>>6);
}
static int await_lock(const char *phase) {
 unsigned stable=0;
 for(unsigned i=0;i<600;i++) {
  int r=locked();if(r<0)return -1;
  stable=r?stable+1:0;
  if(stable==5) {xil_printf("CLOCK %s PASS\r\n",phase);return 0;}
  usleep(100000);
 }
 xil_printf("CLOCK %s TIMEOUT\r\n",phase);return -1;
}
static int ready(void) {
 for(unsigned i=0;i<100;i++) {
  csr_write(0x18,1);if((csr_read(0x1c)&0x7f)==0x7f)return 0;
  usleep(100000);
 }
 xil_printf("CLOCK GTH_TIMEOUT\r\n");return -1;
}
static int verify_phy(void) {
 usleep(300000);csr_write(0x18,1);
 u32 b=csr_read(0x20),r=csr_read(0x24),t=csr_read(0x28),e=csr_read(0x2c);
 usleep(500000);csr_write(0x18,1);
 u32 db=csr_read(0x20)-b,dr=csr_read(0x24)-r,dt=csr_read(0x28)-t,de=csr_read(0x2c)-e;
 u32 er=dr>db?dr-db:db-dr,et=dt>db?dt-db:db-dt;
 if(db<1000000||db>2000000000u||er>db/1000||et>db/1000||de) {
  xil_printf("CLOCK PHY_FAIL %u %u %u %u\r\n",db,dr,dt,de);return -1;
 }
 xil_printf("CLOCK PHY_PASS %u %u %u %u\r\n",db,dr,dt,de);return 0;
}
static int reacquire(void) {
 xil_printf("CLOCK BOOTSTRAP\r\n");
 csr_write(0x34,1);csr_write(0x30,1);
 if(await_lock("PS_LOCK"))return -1;
 csr_write(4,1);usleep(50000);csr_write(4,0);
 if(ready())return -1;
 csr_write(0x34,0);
 if(await_lock("RX_LOCK")||verify_phy())return -1;
 xil_printf("CLOCK LOCKED\r\n");return 0;
}
static int restore(void) {
 if(!changed)return 0;
 csr_write(0x30,0);csr_write(0x34,0);
 if(preamble())return -1;
 for(unsigned i=0;i<NPROFILE;i++)if(checked(clock_profile[i].reg,saved[i]))return -1;
 if(finish()||checked(0x540,saved_control[0])||checked(0xb24,saved_control[1])||checked(0xb25,saved_control[2]))return -1;
 xil_printf("CLOCK RESTORED\r\n");return 0;
}
int main(void) {
 unsigned base=0xff020000;u8 lo,hi;
 XIicPs_Config *cfg=XIicPs_LookupConfig(base);
 if(!cfg||XIicPs_CfgInitialize(&bus,cfg,base)!=XST_SUCCESS||XIicPs_SetSClk(&bus,100000)!=XST_SUCCESS)return 1;
 if(csr_read(0)!=0x44525430||readreg(2,&lo)||readreg(3,&hi)||lo!=0x42||hi!=0x53)goto fail;
 for(unsigned i=0;i<sizeof(factory_plan)/sizeof(factory_plan[0]);i++) {
  u8 value;if(readreg(factory_plan[i].reg,&value)||value!=factory_plan[i].value) {
   xil_printf("CLOCK FACTORY_PLAN_FAIL %04x\r\n",factory_plan[i].reg);goto fail;
  }
 }
 for(unsigned i=0;i<NPROFILE;i++)if(readreg(clock_profile[i].reg,&saved[i]))goto fail;
 if(readreg(0x540,&saved_control[0])||readreg(0xb24,&saved_control[1])||readreg(0xb25,&saved_control[2]))goto fail;
 csr_write(8,0);csr_write(0xc,2);csr_write(0x10,1);csr_write(0x14,1);
 csr_write(0x34,1);csr_write(0x30,1);
 changed=1;
 if(preamble())goto fail;
 for(unsigned i=0;i<NPROFILE;i++)if(checked(clock_profile[i].reg,clock_profile[i].value))goto fail;
 if(finish()||reacquire())goto fail;
 while(1) {
  if(XUartPs_IsReceiveData(STDIN_BASEADDRESS)) {
   char c=XUartPs_RecvByte(STDIN_BASEADDRESS);
   if(c=='Q') {if(restore())goto fail;break;}
   if(c=='L') {
    /* Physical negative control: remove IN0 for one second. */
    csr_write(0x30,0);usleep(1000000);
    int r=locked();if(r<0)goto fail;
    if(r) {xil_printf("CLOCK LOSS_NOT_DETECTED\r\n");goto fail;}
    xil_printf("CLOCK LOSS\r\n");
    if(reacquire())goto fail;
   }
  }
  int r=locked();if(r<0)goto fail;
  if(!r) {xil_printf("CLOCK LOSS\r\n");if(reacquire())goto fail;}
  usleep(100000);
 }
 while(1)usleep(1000000);
fail:
 xil_printf("CLOCK FAIL\r\n");
 if(restore())xil_printf("CLOCK RESTORE_FAIL\r\n");
 while(1)usleep(1000000);
}
