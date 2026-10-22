/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "../diagnostics/ddr/spd_xiicps.h"
static int busy,starts,disabled,callbacks;static u32 event;static unsigned platform=1;
unsigned XGetPlatform_Info(void) {return platform;}
int XIicPs_BusIsBusy(XIicPs *d) {(void)d;return busy;}
void XIicPs_SetStatusHandler(XIicPs *d,void *ref,void (*fn)(void *,u32)) {d->ref=ref;d->handler=fn;callbacks++;}
void XIicPs_MasterRecv(XIicPs *d,u8 *p,s32 n,u16 addr) {(void)p;assert(n==128 && addr==0x51);d->RecvByteCount=n;starts++;}
void XIicPs_MasterSend(XIicPs *d,u8 *p,s32 n,u16 addr) {assert(*p==0 && n==1 && (addr==0x36 || addr==0x51));d->SendByteCount=n;starts++;}
void XIicPs_MasterInterruptHandler(XIicPs *d) {if(event)d->handler(d->ref,event);}
void XIicPs_DisableAllInterrupts(uintptr_t base) {assert(base==0xff030000);disabled++;}
static XIicPs device(void) {XIicPs d={0};d.Config.BaseAddress=0xff030000;d.IsReady=XIL_COMPONENT_IS_READY;return d;}
int main(void) {
 struct spd_xiicps a;struct spd_transport t;XIicPs d=device();u8 bytes[128]={0};
 assert(spd_amd_bind(&a,&d,0,&t)==-1 && callbacks==0);
 platform=4;assert(spd_amd_bind(&a,&d,1,&t)==-1 && callbacks==0);platform=1;
 d.Config.BaseAddress++;assert(spd_amd_bind(&a,&d,1,&t)==-1);d=device();
 d.IsRepeatedStart=1;assert(spd_amd_bind(&a,&d,1,&t)==-1);d=device();
 d.Is10BitAddr=1;assert(spd_amd_bind(&a,&d,1,&t)==-1);d=device();
 busy=1;assert(spd_amd_bind(&a,&d,1,&t)==-1);busy=0;
 assert(spd_amd_bind(&a,&d,1,&t)==0);
 assert(t.begin(t.ctx,SPD_READ,0x50,bytes,128)==-1 && starts==0);
 assert(t.begin(t.ctx,SPD_READ,0x51,bytes,128)==0);
 assert(t.begin(t.ctx,SPD_READ,0x51,bytes,128)==-1 && starts==1);
 assert(t.poll(t.ctx)==0);event=XIICPS_EVENT_COMPLETE_RECV;d.RecvByteCount=0;
 busy=1;assert(t.poll(t.ctx)==0 && t.idle(t.ctx)==0);busy=0;
 assert(t.poll(t.ctx)==1 && disabled==1 && t.idle(t.ctx)==1);
 assert(t.begin(t.ctx,SPD_OFFSET,0x51,bytes,1)==0);
 event=XIICPS_EVENT_COMPLETE_SEND|XIICPS_EVENT_NACK;
 assert(t.poll(t.ctx)==-1 && a.poisoned && t.idle(t.ctx)==0);
 assert(t.begin(t.ctx,SPD_LOWER_PAGE,0x36,bytes,1)==-1);
 event=0;d=device();assert(spd_amd_bind(&a,&d,1,&t)==0);
 assert(t.begin(t.ctx,SPD_READ,0x51,bytes,128)==0);event=XIICPS_EVENT_COMPLETE_RECV;
 assert(t.poll(t.ctx)==-1 && a.poisoned); /* residual count: incomplete */
 puts("AMD SPD adapter mocked API controls PASS; vendor ISR/HW not executed");
}
