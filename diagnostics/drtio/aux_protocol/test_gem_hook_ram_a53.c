/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Linux-user A53 ONLY. All recovery symbols below are RAM-only sentinels. */
#include "netif/xemacpsif.h"
#include "master_network_fault_latch.h"
#ifndef GEM_HOOK_EXPECT_ENABLED
#define GEM_HOOK_EXPECT_ENABLED 1
#endif
struct mnf_latch mnf_copy_only_gem_fault=MNF_LATCH_INITIALIZER;
static struct xemac_s fake;
static xemacpsif_s fake_state;
static char events[8];static unsigned count;
static void check(int condition){if(!condition){register long x0 __asm__("x0")=99;register long x8 __asm__("x8")=93;__asm__ volatile("svc #0"::"r"(x0),"r"(x8):"memory");__builtin_unreachable();}}
static void record(char event){check(mnf_seen(&mnf_copy_only_gem_fault)==GEM_HOOK_EXPECT_ENABLED);check(count<sizeof(events));events[count++]=event;}
void HandleEmacPsError(struct xemac_s *arg){check(arg==&fake);record('H');}
void HandleTxErrors(struct xemac_s *arg){check(arg==&fake);record('T');}
void emacps_recv_handler(void *arg){check(arg==&fake);record('R');}
void setup_rx_bds(xemacpsif_s *arg,XEmacPs_BdRing *ring){check(arg==&fake_state&&ring==&XEmacPs_GetRxRing(&fake_state.emacps));record('B');}
void xemacps_process_sent_bds(xemacpsif_s *arg,XEmacPs_BdRing *ring){check(arg==&fake_state&&ring==&XEmacPs_GetTxRing(&fake_state.emacps));record('S');}
struct test_case {u8 direction;u32 error;const char *events;};
static const struct test_case tests[]={
 {XEMACPS_RECV,0,""},{XEMACPS_RECV,8,"H"},{XEMACPS_RECV,4,"RB"},{XEMACPS_RECV,1,"RB"},{XEMACPS_RECV,13,"HRBRB"},
 {XEMACPS_SEND,256,"H"},{XEMACPS_SEND,64,"T"},{XEMACPS_SEND,16,"T"},{XEMACPS_SEND,4,"T"},{XEMACPS_SEND,2,"S"},{XEMACPS_SEND,342,"HTTTS"},
 {0,1,""},{XEMACPS_SEND,0x80000000u,""}
};
static void pass(void){static const char msg[]="A53_GEM_HOOK_RAM_PASS\n";register long x0 __asm__("x0")=1;register const char *x1 __asm__("x1")=msg;register long x2 __asm__("x2")=sizeof(msg)-1;register long x8 __asm__("x8")=64;__asm__ volatile("svc #0"::"r"(x0),"r"(x1),"r"(x2),"r"(x8):"memory");}
long gem_hook_test_main(const unsigned long *stack){
 check(stack[0]==2);const char *arg=((const char *const *)(stack+1))[1];unsigned index=0;check(*arg);
 while(*arg){check(*arg>='0'&&*arg<='9');index=index*10+(unsigned)(*arg++-'0');check(index<13);}
 fake.state=&fake_state;check(!mnf_seen(&mnf_copy_only_gem_fault));
 emacps_error_handler(&fake,tests[index].direction,tests[index].error);
 check(mnf_seen(&mnf_copy_only_gem_fault)==(GEM_HOOK_EXPECT_ENABLED&&tests[index].error!=0));
 unsigned n=0;while(tests[index].events[n]){check(n<count&&events[n]==tests[index].events[n]);n++;}check(n==count);
 pass();return 0;
}
__asm__(".global _start\n_start:\nmov x0, sp\nbl gem_hook_test_main\nmov x8, #93\nsvc #0\n");
