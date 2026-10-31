/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Explicit host doubles; no MMIO or MicroBlaze instructions. */
#include <assert.h>
#include <setjmp.h>
#include <string.h>
#include "pit_digest_compose.h"
#include "pit_ro_adapter.h"
#include "pit_irq_audit.h"
#include "pit_mailbox_publish_audit.h"
static jmp_buf end;
static unsigned prepares,mailboxes,entered,read_calls;
static int fail_prepare,fail_mailbox;
int pit_mmio_read(void *c,uint32_t a,uint32_t *v){(void)c;(void)a;(void)v;return 0;}
int pit_ro_prepare(struct pit_ro_adapter *s,pit_read_fn r,void *c){assert(s&&r==pit_mmio_read&&!c);prepares++;return fail_prepare;}
int pit_ro_read(void *s,uint32_t a,uint32_t *v){assert(s&&a==0xffd40044);*v=7;read_calls++;return 0;}
int pit_irq_msr_audit(void *c,uint32_t *v){(void)c;(void)v;return 0;}
int pit_irq_disable_audit(void *c){(void)c;return 0;}
int pit_mailbox_prepare_audit(void){mailboxes++;return fail_mailbox;}
int pit_mailbox_sample_write_audit(void *c,uint32_t a,uint32_t v){(void)c;(void)a;(void)v;return 0;}
int pit_mailbox_terminal_write_audit(void *c,uint32_t a,uint32_t v){(void)c;(void)a;(void)v;return 0;}
int pit_mailbox_sample_barrier_audit(void *c){(void)c;return 0;}
int pit_mailbox_terminal_barrier_audit(void *c){(void)c;return 0;}
__attribute__((noreturn)) void pit_terminal_audit(void){longjmp(end,1);}
int pit_digest_compose(struct pit_digest_plan *p){
 uint32_t v=0;
 assert(p->ops.msr==pit_irq_msr_audit&&p->ops.disable==pit_irq_disable_audit);
 assert(p->ops.write==pit_mailbox_sample_write_audit&&p->ops.barrier==pit_mailbox_sample_barrier_audit);
 assert(p->receipt_write==pit_mailbox_terminal_write_audit&&p->receipt_barrier==pit_mailbox_terminal_barrier_audit);
 assert(p->ops.read((void*)1,0xffd40044,&v)==-1);assert(!read_calls);
 assert(p->ops.read(0,0xffd40044,&v)==0&&v==7&&read_calls==1);
 entered++;return 0;
}
extern __attribute__((noreturn)) void pit_digest_root_audit(struct pit_digest_plan *);
int main(void){
 static struct pit_digest_plan p,before;static uint32_t image[8]={1};static unsigned test;
 for(test=0;test<13;test++){
  memset(&p,0,sizeof p);p.nonce=7;p.image_digest=image;
  prepares=mailboxes=entered=read_calls=0;fail_prepare=fail_mailbox=0;
  switch(test){
  case 1:fail_prepare=1;break;case 2:fail_mailbox=1;break;
  case 3:p.consumed=1;break;case 4:p.nonce=0;break;case 5:p.image_digest=0;break;
  case 6:p.capture_context=(void*)1;break;case 7:p.ops.msr=pit_irq_msr_audit;break;
  case 8:p.receipt_write=pit_mailbox_terminal_write_audit;break;
  case 9:p.record.final_msr=1;break;case 10:p.lifecycle_status=1;break;
  case 11:p.metadata_status=-1;break;case 12:p.publication_status=1;break;
  }
  before=p;if(!setjmp(end))pit_digest_root_audit(&p);
  assert(entered==(test==0));assert(prepares==(test<3));assert(mailboxes==(test==0||test==2));
  if(test)assert(!memcmp(&before,&p,sizeof p));
 }
 return 0;
}
