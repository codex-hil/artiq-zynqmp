/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_star_setup.h"
struct star_mock {struct mst_table *setup;unsigned sends,polls,mode,stage;};
static int star_send(void *ctx,const uint8_t *p,size_t n){
 struct star_mock *m=ctx;unsigned stage=m->sends++;
 assert(stage<257&&m->setup->completed==stage&&m->setup->tx.commit_attempted==1);
 if(stage<256){
  assert(n==40&&p[0]==0x30&&p[1]==stage);
  for(unsigned i=0;i<32;i++){
   unsigned expected=0xff;if(stage==0&&i==0)expected=0;if(stage==1&&i==0)expected=1;if(stage==1&&i==1)expected=0;
   assert(p[2+i]==expected);
  }
 }else assert(n==8&&p[0]==0x31&&p[1]==1);
 m->polls=0;return stage==m->stage&&m->mode==1?-1:0;
}
static int star_recv(void *ctx,uint32_t *kind){
 struct star_mock *m=ctx;unsigned stage=m->sends-1;m->polls++;assert(m->polls<=3);
 if(stage==m->stage){if(m->mode==2)return 0;if(m->mode==3){*kind=1;return 1;}if(m->mode==4)return -1;}
 if(m->polls<3)return 0;
 *kind=0x32;return 1;
}
static void star_case(unsigned stage,unsigned mode){
 struct mst_table setup;mst_init_epoch(&setup);struct star_mock m={&setup,0,0,mode,stage};struct mr_io io={&m,star_send,star_recv};
 const int expected[5]={MT_OK,MT_IO,MT_TIMEOUT,MT_UNEXPECTED,MT_PACKET};
 assert(mst_run_once(&setup,&io,3)==expected[mode]);
 assert(setup.completed==(mode?stage:257)&&m.sends==(mode?stage+1:257));
 assert(setup.send_attempts==m.sends);
 unsigned sends=m.sends,polls=m.polls;
 assert(mst_run_once(&setup,&io,3)==MT_BUSY&&m.sends==sends&&m.polls==polls);
 if(mode)assert(mt_next_after_success(&setup.tx)==MT_INVALID);
}
int master_star_setup_test(void){
 star_case(0,0);unsigned cases=1;
 for(unsigned stage=0;stage<257;stage++)for(unsigned mode=1;mode<5;mode++){star_case(stage,mode);cases++;}
 struct mt_transaction t;mt_init_new_epoch(&t);assert(mt_next_after_success(&t)==MT_INVALID);
 assert(mt_begin(&t,0x30,3)==0&&mt_next_after_success(&t)==MT_INVALID);
 assert(mt_tx_complete(&t,1)==0&&mt_next_after_success(&t)==MT_INVALID);
 printf("MASTER_STAR_SETUP_PASS cases=%u stages=257\n",cases);return 0;
}
