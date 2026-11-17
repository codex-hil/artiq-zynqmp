/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_transaction.h"
int main(void) {
 unsigned cases=0;
 for(unsigned request=0x30;request<=0x31;request++)for(unsigned budget=1;budget<=64;budget++) {
  struct mt_transaction t;mt_init_new_epoch(&t);
  assert(mt_begin(&t,request,budget)==0&&t.commit_attempted==1);
  assert(mt_begin(&t,request,budget)==MT_BUSY);
  assert(mt_poll(&t,1,0x32)==MT_INVALID); /* ACK before TX outcome rejected */
  assert(mt_tx_complete(&t,1)==0);
  for(unsigned i=1;i<budget;i++)assert(mt_poll(&t,0,0)==0&&t.state==MT_WAIT);
  assert(mt_poll(&t,1,0x32)==0&&t.state==MT_DONE);
  assert(mt_begin(&t,request,budget)==MT_BUSY);cases++;
 }
 for(unsigned errorcase=0;errorcase<4;errorcase++) {
  struct mt_transaction t;mt_init_new_epoch(&t);assert(mt_begin(&t,0x30,2)==0);
  if(errorcase==0)assert(mt_tx_complete(&t,0)==MT_IO);
  else {
   assert(mt_tx_complete(&t,1)==0);
   if(errorcase==1)assert(mt_poll(&t,1,1)==MT_UNEXPECTED);
   if(errorcase==2)assert(mt_poll(&t,-1,0)==MT_PACKET);
   if(errorcase==3){assert(mt_poll(&t,0,0)==0);assert(mt_poll(&t,0,0)==MT_TIMEOUT);}
  }
  assert(t.state==MT_FAILED&&t.commit_attempted==1);
  assert(mt_poll(&t,1,0x32)==MT_INVALID&&t.state==MT_FAILED); /* late ACK */
  assert(mt_begin(&t,0x31,2)==MT_BUSY);cases++;
 }
 struct mt_transaction t;mt_init_new_epoch(&t);
 assert(mt_begin(&t,0x30,0)==MT_INVALID&&t.state==MT_IDLE);
 assert(mt_begin(&t,0x30,4097)==MT_INVALID&&t.state==MT_IDLE);
 assert(mt_begin(&t,0x32,2)==MT_INVALID&&t.state==MT_IDLE);
 assert(mt_begin(0,0x30,2)==MT_INVALID);assert(mt_tx_complete(0,1)==MT_INVALID);
 assert(mt_poll(0,0,0)==MT_INVALID);mt_init_new_epoch(0);
 printf("MASTER_TRANSACTION_POLICY_PASS %u scenarios plus invalid arguments\n",cases);
 return 0;
}
