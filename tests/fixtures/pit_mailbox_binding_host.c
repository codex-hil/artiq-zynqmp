/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Test double for terminal transfer and target wrapper functions, no MMIO. */
#include <assert.h>
#include <setjmp.h>
#include <string.h>
#include "pit_status_compose.h"
#include "pit_mailbox_publish_audit.h"
static jmp_buf end;
static unsigned prepare_calls,entered;
static int preparation_fails;
static uint32_t digest[8]={1};
static int msr(void *c,uint32_t *v){(void)c;*v=0x104;return 0;}
static int disable(void *c){(void)c;return 0;}
int pit_mailbox_prepare_audit(void){++prepare_calls;return preparation_fails;}
int pit_mailbox_sample_write_audit(void *c,uint32_t o,uint32_t v){(void)c;(void)o;(void)v;return 0;}
int pit_mailbox_terminal_write_audit(void *c,uint32_t o,uint32_t v){(void)c;(void)o;(void)v;return 0;}
int pit_mailbox_sample_barrier_audit(void *c){(void)c;return 0;}
int pit_mailbox_terminal_barrier_audit(void *c){(void)c;return 0;}
__attribute__((noreturn)) void pit_terminal_audit(void){longjmp(end,1);}
__attribute__((noreturn)) void pit_mmio_composition_audit(struct pit_status_audit_plan *p){
 assert(!p->capture_context && !p->receipt_context && !p->capture_ops.read);
 assert(p->capture_ops.write==pit_mailbox_sample_write_audit);
 assert(p->capture_ops.barrier==pit_mailbox_sample_barrier_audit);
 assert(p->receipt_write==pit_mailbox_terminal_write_audit);
 assert(p->receipt_barrier==pit_mailbox_terminal_barrier_audit);
 ++entered;longjmp(end,1);
}
extern __attribute__((noreturn)) void pit_mailbox_composition_audit(struct pit_status_audit_plan *);
int main(void){
 static struct pit_status_audit_plan p,before;
 static struct pit_ro_adapter adapter;
 static unsigned test;
 for(test=0;test<20;test++){
  memset(&p,0,sizeof p);memset(&adapter,0,sizeof adapter);
  p.read_adapter=&adapter;p.nonce=7;p.image_digest=digest;p.sample_digest=digest;
  p.capture_ops.msr=msr;p.capture_ops.disable=disable;
  prepare_calls=entered=0;preparation_fails=0;
  switch(test){
   case 0:break;
   case 1:preparation_fails=1;break;
   case 2:p.capture_context=(void *)1;break;
   case 3:p.receipt_context=(void *)1;break;
   case 4:p.capture_ops.write=pit_mailbox_terminal_write_audit;break;
   case 5:p.receipt_write=pit_mailbox_sample_write_audit;break;
   case 6:p.capture_ops.barrier=pit_mailbox_terminal_barrier_audit;break;
   case 7:p.receipt_barrier=pit_mailbox_sample_barrier_audit;break;
   case 8:p.consumed=1;break;
   case 9:p.capture.consumed=1;break;
   case 10:p.publication.consumed=1;break;
   case 11:p.record.commit=1;break;
   case 12:p.nonce=0;break;
   case 13:p.image_digest=0;break;
   case 14:p.sample_digest=0;break;
   case 15:p.capture_ops.msr=0;break;
   case 16:p.capture_ops.disable=0;break;
   case 17:adapter.armed=1;break;
   case 18:adapter.busy=1;break;
   case 19:p.read_adapter=0;break;
  }
  before=p;
  if(!setjmp(end))pit_mailbox_composition_audit(&p);
  assert(entered==(test==0));assert(prepare_calls==(test<2));
  if(test)assert(memcmp(&p,&before,sizeof p)==0);
 }
 prepare_calls=entered=0;
 if(!setjmp(end))pit_mailbox_composition_audit(0);
 assert(!prepare_calls && !entered);
 return 0;
}
