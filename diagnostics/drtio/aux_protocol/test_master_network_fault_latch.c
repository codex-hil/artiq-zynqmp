/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <pthread.h>
#include <stdio.h>
#include "master_network_fault_observer.h"
static struct mnf_latch concurrent=MNF_LATCH_INITIALIZER;
static void *producer(void *arg){(void)arg;for(unsigned i=0;i<20000;i++)mnf_publish(&concurrent);return 0;}
int main(void){
 unsigned cases=0;
 for(unsigned gap=0;gap<=4;gap++){
  struct mnf_latch latch=MNF_LATCH_INITIALIZER;
  for(unsigned step=0;step<=4;step++){
   if(step==gap)mnf_publish(&latch);
   if(step<4)assert(mnf_seen(&latch)==(step>=gap));
  }
  assert(mnf_seen(&latch));for(unsigned i=0;i<10;i++){mnf_publish(&latch);assert(mnf_seen(&latch));}cases++;
 }
 for(unsigned receipts=0;receipts<16;receipts++){
  struct mnf_latch latch=MNF_LATCH_INITIALIZER;struct mnf_view view={&latch,9,receipts};struct mnh_health out={17,18,19};
  int r=mnf_observe(&view,&out);
  if(receipts==7){assert(!r&&out.generation==9&&out.receipts==7&&!out.fault);mnf_publish(&latch);assert(!mnf_observe(&view,&out)&&out.fault==1);}
  else assert(r==-1&&out.generation==17&&out.receipts==18&&out.fault==19);
  cases++;
 }
 {struct mnf_latch latch=MNF_LATCH_INITIALIZER;struct mnf_view v={&latch,0,7};struct mnh_health h={17,18,19};
  assert(mnf_observe(&v,&h)==-1&&h.generation==17);v.generation=9;v.latch=0;assert(mnf_observe(&v,&h)==-1);assert(mnf_observe(0,&h)==-1&&mnf_observe(&v,0)==-1);cases++;
 }
 {struct mnf_latch latch=MNF_LATCH_INITIALIZER;const struct mnf_view v={&latch,9,7};struct mnh_health h;
  struct mfo_gate gate={0};mfo_init(&gate);assert(!mfo_fresh_epoch(&gate,1,15)&&!mfo_request_master(&gate)&&!mfo_grant_master(&gate,7));
  struct mne_policy policy={0};assert(!mnf_observe((void *)&v,&h)&&!mne_begin(&policy,&gate,gate.ticket,h.generation,h.receipts,h.fault));
  uint64_t ticket=gate.ticket;mnf_publish(&latch);assert(!mnf_observe((void *)&v,&h)&&mne_observe(&policy,h.generation,h.receipts,h.fault)==MNE_UNSAFE&&!mne_ready(&policy)&&gate.state==MFO_FAULT&&gate.ticket==ticket);
  assert(!mnf_observe((void *)&v,&h)&&h.fault&&mne_observe(&policy,h.generation,h.receipts,h.fault)==MNE_UNSAFE);cases++;
 }
 pthread_t threads[4];for(unsigned i=0;i<4;i++)assert(!pthread_create(&threads[i],0,producer,0));
 unsigned observed=0;for(unsigned i=0;i<100000;i++){unsigned value=mnf_seen(&concurrent);assert(!observed||value);observed|=value;}
 for(unsigned i=0;i<4;i++){assert(!pthread_join(threads[i],0));}
 assert(mnf_seen(&concurrent));cases++;
 printf("NETWORK_FAULT_LATCH_PASS cases=%u producers=4 stores=80000 reads=100000\n",cases);return 0;
}
