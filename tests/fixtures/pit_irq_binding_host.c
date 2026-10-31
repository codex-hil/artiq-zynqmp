/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Explicit transfer/callback doubles, no target instructions or MMIO. */
#include <assert.h>
#include <setjmp.h>
#include <string.h>
#include "pit_status_compose.h"
#include "pit_irq_audit.h"
static jmp_buf end;
static unsigned entered;
int pit_irq_msr_audit(void *c,uint32_t *v){(void)c;(void)v;return 0;}
int pit_irq_disable_audit(void *c){(void)c;return 0;}
__attribute__((noreturn)) void pit_terminal_audit(void){longjmp(end,1);}
__attribute__((noreturn)) void pit_mailbox_composition_audit(struct pit_status_audit_plan *p){
 assert(p->capture_ops.msr==pit_irq_msr_audit);
 assert(p->capture_ops.disable==pit_irq_disable_audit);
 assert(!p->capture_ops.read && !p->capture_ops.write && !p->receipt_write);
 entered++;longjmp(end,1);
}
extern __attribute__((noreturn)) void pit_irq_composition_audit(struct pit_status_audit_plan *);
int main(void){
 static struct pit_status_audit_plan p,before;static struct pit_ro_adapter adapter;
 static uint32_t digest[8]={1};static unsigned test;
 for(test=0;test<13;test++){
  memset(&p,0,sizeof p);memset(&adapter,0,sizeof adapter);entered=0;
  p.read_adapter=&adapter;p.nonce=7;p.image_digest=p.sample_digest=digest;
  switch(test){
  case 1:p.capture_ops.msr=pit_irq_msr_audit;break;
  case 2:p.capture_ops.disable=pit_irq_disable_audit;break;
  case 3:p.capture_context=(void*)1;break;
  case 4:p.receipt_context=(void*)1;break;
  case 5:p.consumed=1;break;
  case 6:p.capture.consumed=1;break;
  case 7:p.publication.consumed=1;break;
  case 8:p.record.commit=1;break;
  case 9:adapter.failed=1;break;
  case 10:adapter.attempted=1;break;
  case 11:p.nonce=0;break;
  case 12:p.read_adapter=0;break;
  }
  before=p;
  if(!setjmp(end))pit_irq_composition_audit(&p);
  assert(entered==(test==0));
  if(test)assert(!memcmp(&before,&p,sizeof p));
 }
 entered=0;if(!setjmp(end))pit_irq_composition_audit(0);assert(!entered);
 return 0;
}
