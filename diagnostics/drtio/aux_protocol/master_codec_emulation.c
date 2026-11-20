/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* QEMU Linux-user test ONLY. Syscalls are not an A53 board panic/runtime ABI. */
#include "master_leaf_codec.h"
static void message(const char *p,unsigned n){
 register uint64_t x0 __asm__("x0")=1,x1 __asm__("x1")=(uintptr_t)p,x2 __asm__("x2")=n,x8 __asm__("x8")=64;
 __asm__ volatile("svc 0":"+r"(x0):"r"(x1),"r"(x2),"r"(x8):"memory");
}
__attribute__((noreturn))static void finish(unsigned code){
 register uint64_t x0 __asm__("x0")=code,x8 __asm__("x8")=93;
 __asm__ volatile("svc 0"::"r"(x0),"r"(x8):"memory");__builtin_unreachable();
}
__attribute__((noreturn))void aux_master_panic(void){
 static const char text[]="A53_CODEC_EMULATOR_PANIC\n";message(text,sizeof(text)-1);finish(101);
}
static void check(int condition){if(!condition)finish(99);}
#if defined(MASTER_ROUTE_EMULATION) || defined(MASTER_FULL_SETUP_EMULATION) || defined(MASTER_WHOLE_COOPERATIVE_EMULATION) || defined(MASTER_FOREGROUND_EMULATION) || defined(MASTER_RESUMABLE_EMULATION)
void master_emulation_assert(int condition){check(condition);}
#endif
#ifdef MASTER_ROUTE_EMULATION
extern int master_mmio_route_test(const uint8_t *,size_t);
void master_emulation_route_pass(void){
 static const char text[]="A53_ROUTE_EMULATION_PASS faults=63 controls=4\n";message(text,sizeof(text)-1);
}
#endif
#ifdef MASTER_FULL_SETUP_EMULATION
extern int master_full_setup_composition_test(const uint8_t *,size_t);
void master_emulation_full_setup_pass(void){
 static const char text[]="A53_FULL_SETUP_EMULATION_PASS cases=16 sends=259 pops=260\n";message(text,sizeof(text)-1);
}
#endif
#ifdef MASTER_WHOLE_COOPERATIVE_EMULATION
extern int master_setup_cooperative_test(const uint8_t *,size_t);
void master_emulation_setup_cooperative_pass(unsigned maximum){
 check(maximum==22);
 static const char text[]="A53_COOPERATIVE_SETUP_EMULATION_PASS cases=22 healthy_turns=522 max_mock_ops=22\n";message(text,sizeof(text)-1);
}
#endif
#ifdef MASTER_FOREGROUND_EMULATION
extern int master_foreground_composition_test(const uint8_t *,size_t);
void master_emulation_foreground_pass(unsigned cases){
 check(cases==8);
 static const char text[]="A53_FOREGROUND_COMPOSITION_PASS cases=8 healthy_turns=522\n";message(text,sizeof(text)-1);
}
#endif
#ifdef MASTER_RESUMABLE_EMULATION
extern int master_resumable_composition_test(const uint8_t *,size_t);
void master_emulation_resumable_pass(unsigned cases,unsigned maximum){
 check(cases==69&&maximum==1);
 static const char text[]="A53_RESUMABLE_COMPOSITION_PASS cases=69 healthy_turns=550 max_rt_callbacks=1\n";message(text,sizeof(text)-1);
}
#endif
int codec_emulation_main(void){
#ifdef FORCE_PANIC
 aux_master_panic();
#endif
 uint8_t out[1026];unsigned calls=0;
 for(unsigned kind=0x30;kind<=0x31;kind++){
  unsigned required=kind==0x30?40:8;
  for(unsigned capacity=0;capacity<=1025;capacity++){
   for(unsigned i=0;i<1026;i++)out[i]=0xa5;
   int n=aux_master_leaf_encode(kind,1,out,capacity);calls++;
   if(capacity<required||capacity>1024){check(n==-4);for(unsigned i=0;i<1026;i++)check(out[i]==0xa5);}
   else{check(n==(int)required&&out[0]==kind&&out[1]==1);for(unsigned i=required;i<1026;i++)check(out[i]==0xa5);}
  }
  for(unsigned value=0;value<4096;value++){
   int n=aux_master_leaf_encode(kind,value,out,1024);calls++;
   check(n==(value==1?(int)required:-2));
  }
 }
 /* RoutingAck fixture generated using the same IEEECRC envelope as upstream;
  * host upstream byte-vector assertion is recorded separately by the runner. */
 const uint8_t ack[8]=ACK_BYTES;
 check(aux_master_routing_ack_decode(ack,8)==0x32);calls++;
 for(unsigned bit=0;bit<64;bit++){
  for(unsigned i=0;i<8;i++){out[i]=ack[i];}
  out[bit/8]^=(uint8_t)(1u<<(bit%8));
  check(aux_master_routing_ack_decode(out,8)==-1);calls++;
 }
 for(unsigned n=0;n<=1025;n++)if(n!=8){check(aux_master_routing_ack_decode(out,n)==-4);calls++;}
 check(calls==11334);
#ifdef MASTER_ROUTE_EMULATION
 check(master_mmio_route_test(ack,sizeof(ack))==0);
#endif
#ifdef MASTER_FULL_SETUP_EMULATION
 const uint8_t frames[40]=SETUP_FRAMES;
 check(master_full_setup_composition_test(frames,sizeof(frames))==0);
#endif
#ifdef MASTER_WHOLE_COOPERATIVE_EMULATION
 const uint8_t frames[40]=SETUP_FRAMES;
 check(master_setup_cooperative_test(frames,sizeof(frames))==0);
#endif
#ifdef MASTER_FOREGROUND_EMULATION
 const uint8_t frames[40]=SETUP_FRAMES;
 check(master_foreground_composition_test(frames,sizeof(frames))==0);
#endif
#ifdef MASTER_RESUMABLE_EMULATION
 const uint8_t frames[40]=SETUP_FRAMES;
 check(master_resumable_composition_test(frames,sizeof(frames))==0);
#endif
 static const char text[]="A53_CODEC_EMULATION_PASS calls=11334\n";message(text,sizeof(text)-1);return 0;
}
__asm__(".global _start\n_start:\nbl codec_emulation_main\nmov x8,#93\nsvc #0\n");
