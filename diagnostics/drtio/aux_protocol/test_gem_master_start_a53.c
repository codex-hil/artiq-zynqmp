/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Linux-user A53 only: copied GEM handler + RAM recovery + real Rust codec. */
#include "netif/xemacpsif.h"
#include "master_network_static.h"
#include "master_network_fault_observer.h"
static void check(int ok){if(!ok){register long x0 __asm__("x0")=99;register long x8 __asm__("x8")=93;__asm__ volatile("svc #0"::"r"(x0),"r"(x8):"memory");__builtin_unreachable();}}
#define assert(condition) check(!!(condition))
#include "master_setup_mock_fixture.h"
struct mnf_latch mnf_copy_only_gem_fault=MNF_LATCH_INITIALIZER;
static struct xemac_s gem;static xemacpsif_s gem_state;
static struct setup_fake bus_state;
static unsigned scenario,injected,published_at,recoveries;
static void recovery(void){check(mnf_seen(&mnf_copy_only_gem_fault));check(bus_state.calls==published_at);recoveries++;}
void HandleEmacPsError(struct xemac_s *p){check(p==&gem);recovery();}
void HandleTxErrors(struct xemac_s *p){check(p==&gem);recovery();}
void emacps_recv_handler(void *p){check(p==&gem);recovery();}
void setup_rx_bds(xemacpsif_s *p,XEmacPs_BdRing *r){check(p==&gem_state&&r==&XEmacPs_GetRxRing(&gem_state.emacps));recovery();}
void xemacps_process_sent_bds(xemacpsif_s *p,XEmacPs_BdRing *r){check(p==&gem_state&&r==&XEmacPs_GetTxRing(&gem_state.emacps));recovery();}
static void inject(void){
 published_at=bus_state.calls;injected=1;
 u32 error=scenario==11?0:scenario==12?0x80000000u:XEMACPS_RXSR_HRESPNOK_MASK;
 emacps_error_handler(&gem,scenario==12?XEMACPS_SEND:XEMACPS_RECV,error);
 check(mnf_seen(&mnf_copy_only_gem_fault)==(error!=0));
}
static void after_bus(unsigned read,uint32_t address){
 if(injected)return;
 if(((scenario==3||scenario==11||scenario==12)&&bus_state.calls==1)||(scenario==4&&bus_state.calls==3)||(scenario==5&&bus_state.tx==1)||(scenario==6&&bus_state.tx==129)||(scenario==7&&bus_state.tx==258)||(scenario==8&&read&&address==MRT_FORCE&&bus_state.tx==259&&bus_state.pops==260&&bus_state.requests==1&&!bus_state.force))inject();
}
static int rd(void *c,uint32_t a,uint32_t *v){(void)c;check(!mnf_seen(&mnf_copy_only_gem_fault));int r=setup_read(&bus_state,a,v);after_bus(1,a);return r;}
static int wr(void *c,uint32_t a,uint32_t v){(void)c;check(!mnf_seen(&mnf_copy_only_gem_fault));int r=setup_write(&bus_state,a,v);after_bus(0,a);return r;}
static int fence(void *c){(void)c;check(!mnf_seen(&mnf_copy_only_gem_fault));int r=setup_fence(&bus_state);after_bus(0,0);return r;}
void aux_master_panic(void){register long x0 __asm__("x0")=101;register long x8 __asm__("x8")=93;__asm__ volatile("svc #0"::"r"(x0),"r"(x8):"memory");__builtin_unreachable();}
static void pass(void){static const char msg[]="A53_GEM_MASTER_START_PASS\n";register long x0 __asm__("x0")=1;register const char *x1 __asm__("x1")=msg;register long x2 __asm__("x2")=sizeof(msg)-1;register long x8 __asm__("x8")=64;__asm__ volatile("svc #0"::"r"(x0),"r"(x1),"r"(x2),"r"(x8):"memory");}
long gem_master_main(const unsigned long *stack){
 (void)action_step;check(stack[0]==2);const char *arg=((const char *const *)(stack+1))[1];check(*arg);
 while(*arg){check(*arg>='0'&&*arg<='9');scenario=scenario*10+(unsigned)(*arg++-'0');check(scenario<13);}
 static const uint8_t frames[]=SETUP_FRAMES;bus_state.frames=frames;gem.state=&gem_state;
 static struct mfo_gate gate;static const struct mnf_view view={&mnf_copy_only_gem_fault,9,7};
 mfo_init(&gate);check(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
 struct mm_bus bus={0,rd,wr,fence};if(scenario==1)inject();
 int result=mns_begin(&gate,gate.ticket,&bus,(void *)&view,mnf_observe,3,64,8730,8827);unsigned turns=0;
 if(scenario==1)check(result==MNE_UNSAFE&&!bus_state.calls);
 else{
  check(!result&&!bus_state.calls);if(scenario==2)inject();
  while(!result){unsigned before=bus_state.calls;result=mns_poll();check(bus_state.calls-before<=1&&++turns<=8830);}
 }
 struct mnh_status out={0};unsigned calls=bus_state.calls;
 if(scenario==0||scenario==9||scenario==10||scenario==11){
  check(result==1&&turns==8830&&bus_state.tx==259&&bus_state.pops==260);
  if(scenario==10)check(!mns_snapshot(&out)&&out.complete&&out.credits==16);
  if(scenario==9||scenario==10)inject();
  int r=mns_snapshot(&out);
  if(scenario==0||scenario==11)check(!r&&out.complete&&out.credits==16&&!recoveries);
  else check(r==MNE_UNSAFE&&!out.complete&&!out.credits&&gate.state==MFO_FAULT);
 }else{
  check(result==MNE_UNSAFE&&mns_snapshot(&out)==MNE_UNSAFE&&!out.complete&&!out.credits&&gate.state==MFO_FAULT&&gate.owner==MFO_MASTER_OWNER);
  if(scenario==1||scenario==2)check(!calls);
  if(scenario==3||scenario==12)check(calls==1);
  if(scenario==4)check(calls==3);
  if(scenario==5)check(bus_state.tx==1);
  if(scenario==6)check(bus_state.tx==129);
  if(scenario==7)check(bus_state.tx==258);
  if(scenario==8){check(turns==8830&&bus_state.tx==259&&bus_state.pops==260);
#ifdef GEM_MASTER_FALSE_READY
   check(out.complete==1); /* Deliberate false success after handler publishes. */
#endif
  }
 }
 check(bus_state.calls==calls);
 if(scenario!=0&&scenario!=11){check(injected&&mnf_seen(&mnf_copy_only_gem_fault)&&calls==published_at);check(recoveries==(scenario==12?0u:1u));check(mns_poll()==MNE_UNSAFE&&mns_snapshot(&out)==MNE_UNSAFE&&!out.complete&&!out.credits&&bus_state.calls==calls);}
 pass();return 0;
}
__asm__(".global _start\n_start:\nmov x0, sp\nbl gem_master_main\nmov x8, #93\nsvc #0\n");
