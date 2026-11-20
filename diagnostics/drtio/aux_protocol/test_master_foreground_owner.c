/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_foreground_owner.h"
static unsigned checks;
#define CHECK(x) do{assert(x);checks++;}while(0)
static struct mfo_gate fresh(void){struct mfo_gate g;mfo_init(&g);CHECK(!mfo_fresh_epoch(&g,1,15));return g;}
static struct mfo_gate master(void){struct mfo_gate g=fresh();CHECK(!mfo_request_master(&g));CHECK(!mfo_grant_master(&g,7));return g;}
int main(void){
 struct mfo_gate g;mfo_init(&g);
 CHECK(mfo_worker_dispatch(&g)==MFO_BUSY);CHECK(mfo_request_master(&g)==MFO_BUSY);
 for(unsigned r=0;r<16;r++)if(r!=15)CHECK(mfo_fresh_epoch(&g,1,r)==MFO_INVALID&&g.state==MFO_CLOSED);
 CHECK(!mfo_fresh_epoch(&g,1,15));CHECK(!mfo_worker_dispatch(&g));uint64_t worker=g.ticket;
 CHECK(!mfo_request_master(&g)&&g.state==MFO_DRAINING&&g.ticket==worker);
 CHECK(mfo_worker_dispatch(&g)==MFO_BUSY);CHECK(mfo_grant_master(&g,7)==MFO_BUSY);
 CHECK(mfo_worker_quiesced(&g,worker,0)==MFO_INVALID&&g.state==MFO_DRAINING);
 CHECK(mfo_worker_quiesced(&g,worker+1,1)==MFO_INVALID);
 CHECK(!mfo_worker_quiesced(&g,worker,1)&&g.state==MFO_WAIT_MASTER);
 CHECK(mfo_worker_dispatch(&g)==MFO_BUSY);
 for(unsigned r=0;r<7;r++)CHECK(mfo_grant_master(&g,r)==MFO_INVALID&&g.state==MFO_WAIT_MASTER);
 CHECK(!mfo_grant_master(&g,7));uint64_t first=g.ticket;
 CHECK(first>worker&&g.owner==MFO_MASTER_OWNER);
 CHECK(mfo_setup_result(&g,worker,1)==MFO_INVALID&&g.state==MFO_MASTER);
 CHECK(!mfo_setup_result(&g,first,0)&&g.state==MFO_MASTER);
 CHECK(mfo_release_master(&g,first,7)==MFO_BUSY);
 CHECK(!mfo_setup_result(&g,first,1)&&g.state==MFO_HELD);
 CHECK(mfo_worker_dispatch(&g)==MFO_BUSY);CHECK(mfo_request_master(&g)==MFO_BUSY);
 for(unsigned r=0;r<8;r++)if(r!=7)CHECK(mfo_release_master(&g,first,r)==MFO_INVALID&&g.state==MFO_HELD);
 CHECK(!mfo_release_master(&g,first,7));CHECK(!mfo_worker_dispatch(&g));
 CHECK(mfo_worker_quiesced(&g,worker,1)==MFO_INVALID);CHECK(!mfo_worker_quiesced(&g,g.ticket,1));
 CHECK(!mfo_request_master(&g)&&!mfo_grant_master(&g,7)&&g.ticket>first);
 CHECK(mfo_release_master(&g,first,7)==MFO_INVALID);
 CHECK(mfo_setup_result(&g,g.ticket,-77)==-77);uint64_t fault_ticket=g.ticket;
 CHECK(mfo_fault(&g,MFO_CANCELLED)==-77&&g.ticket==fault_ticket);
 CHECK(mfo_release_master(&g,g.ticket,7)==MFO_BUSY);CHECK(mfo_worker_dispatch(&g)==MFO_BUSY);
 CHECK(mfo_fresh_epoch(&g,1,15)==MFO_INVALID);
 CHECK(!mfo_fresh_epoch(&g,2,15)&&g.state==MFO_IDLE);CHECK(!mfo_request_master(&g)&&!mfo_grant_master(&g,7));
 CHECK(g.ticket>fault_ticket&&mfo_setup_result(&g,fault_ticket,1)==MFO_INVALID);
 /* Cancellation at every reachable phase holds the original owner/ticket. */
 for(unsigned phase=0;phase<7;phase++){
  g=fresh();
  if(phase==1||phase==2){CHECK(!mfo_worker_dispatch(&g));if(phase==2)CHECK(!mfo_request_master(&g));}
  if(phase==3)CHECK(!mfo_request_master(&g));
  if(phase>=4){g=master();if(phase>=5)CHECK(!mfo_setup_result(&g,g.ticket,1));if(phase==6)CHECK(!mfo_release_master(&g,g.ticket,7));}
  uint64_t ticket=g.ticket;enum mfo_owner owner=g.owner;
  CHECK(mfo_fault(&g,MFO_CANCELLED)==MFO_CANCELLED&&g.ticket==ticket&&g.owner==owner);
  CHECK(mfo_worker_dispatch(&g)==MFO_BUSY&&mfo_request_master(&g)==MFO_BUSY);
  CHECK(mfo_fault(&g,-99)==MFO_CANCELLED);
 }
 g=master();CHECK(mfo_setup_result(&g,g.ticket,2)==MFO_INVALID&&g.state==MFO_FAULT);
 g=fresh();g.serial=UINT64_MAX;CHECK(mfo_worker_dispatch(&g)==MFO_INVALID&&g.state==MFO_FAULT&&g.ticket==0);
 g=fresh();g.serial=UINT64_MAX;CHECK(!mfo_request_master(&g));CHECK(mfo_grant_master(&g,7)==MFO_INVALID&&g.state==MFO_FAULT);
 printf("MASTER_FOREGROUND_OWNER_PASS checks=%u\n",checks);return 0;
}
