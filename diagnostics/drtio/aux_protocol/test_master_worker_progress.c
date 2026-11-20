/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_worker_progress.h"
static unsigned checks;
#define CHECK(x) do{assert(x);checks++;}while(0)
int main(void){
 for(unsigned draining=0;draining<2;draining++)for(unsigned phase=1;phase<=3;phase++)for(unsigned command=0;command<=8;command++){
  struct mfo_gate g;mfo_init(&g);CHECK(!mfo_fresh_epoch(&g,1,15));CHECK(!mwp_new_work(&g,2));
  uint64_t ticket=g.ticket;struct mwp_reply reply={0};
  if(draining)CHECK(!mfo_request_master(&g));
  CHECK(!mwp_arm(&reply,&g,ticket,1,1,(enum mwp_phase)phase,1));
  int allowed=(phase==1&&command==3)||(phase==2&&(command==4||command==7))||(phase==3&&command==6);
  CHECK(mwp_progress_once(&reply,&g,command)==(allowed?0:MFO_INVALID));
  CHECK(g.ticket==ticket&&g.owner==MFO_WORKER_OWNER&&g.state==(draining?MFO_DRAINING:MFO_WORKER));
  CHECK(mfo_grant_master(&g,7)==MFO_BUSY);
  CHECK(mwp_new_work(&g,1)==MFO_BUSY&&mwp_new_work(&g,2)==MFO_BUSY);
  if(allowed)CHECK(mwp_progress_once(&reply,&g,command)==MFO_INVALID);
 }
 struct mfo_gate g;mfo_init(&g);CHECK(!mfo_fresh_epoch(&g,1,15));CHECK(!mwp_new_work(&g,1));uint64_t old=g.ticket;
 struct mwp_reply reply={0};
 CHECK(mwp_arm(&reply,&g,old+1,1,1,MWP_SYNC_REPLY,1)==MFO_INVALID);
 CHECK(mwp_arm(&reply,&g,old,2,1,MWP_SYNC_REPLY,1)==MFO_INVALID);
 CHECK(mwp_arm(&reply,&g,old,1,1,MWP_SYNC_REPLY,0)==MFO_INVALID);
 CHECK(!mwp_arm(&reply,&g,old,1,1,MWP_SYNC_REPLY,1));
 CHECK(mwp_arm(&reply,&g,old,1,2,MWP_ASYNC_REPLY,1)==MFO_BUSY);
 CHECK(!mfo_request_master(&g)&&!mwp_progress_once(&reply,&g,4));
 CHECK(mwp_arm(&reply,&g,old,1,1,MWP_SYNC_REPLY,1)==MFO_INVALID);
 CHECK(!mwp_arm(&reply,&g,old,1,2,MWP_EXCEPTION_ACK,1)&&!mwp_progress_once(&reply,&g,6));
 CHECK(g.state==MFO_DRAINING&&mfo_grant_master(&g,7)==MFO_BUSY);
 CHECK(mwp_abandon(&g,old+1,1,-55)==MFO_INVALID);
 CHECK(!mwp_arm(&reply,&g,old,1,3,MWP_SYNC_REPLY,1));
 CHECK(mwp_abandon(&g,old,1,-55)==-55&&g.state==MFO_FAULT&&g.ticket==old);
 CHECK(mwp_progress_once(&reply,&g,7)==MFO_INVALID);
 CHECK(mfo_worker_quiesced(&g,old,1)==MFO_BUSY&&mfo_grant_master(&g,7)==MFO_BUSY);
 CHECK(!mfo_fresh_epoch(&g,2,15)&&!mwp_new_work(&g,2)&&g.ticket>old);
 CHECK(mwp_progress_once(&reply,&g,4)==MFO_INVALID);
 CHECK(!mwp_arm(&reply,&g,g.ticket,2,4,MWP_SYNC_REPLY,1));
 CHECK(!mfo_request_master(&g)&&!mwp_progress_once(&reply,&g,7));
 CHECK(!mfo_worker_quiesced(&g,g.ticket,1)&&!mfo_grant_master(&g,7));
 CHECK(mwp_arm(&reply,&g,g.ticket,2,5,MWP_SYNC_REPLY,1)==MFO_INVALID);
 CHECK(mwp_progress_once(&reply,&g,4)==MFO_INVALID);
 CHECK(mwp_new_work(&g,3)==MFO_INVALID&&mwp_new_work(&g,5)==MFO_INVALID);
 printf("MASTER_WORKER_PROGRESS_PASS checks=%u matrix_cases=54\n",checks);return 0;
}
