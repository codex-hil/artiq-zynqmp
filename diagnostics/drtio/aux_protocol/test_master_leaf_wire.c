/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "master_leaf_codec.h"
int master_leaf_wire_test(void) {
 uint8_t b[1024];for(unsigned i=0;i<1024;i++)b[i]=0xa5;
 if(aux_master_leaf_encode(0x30,1,b,40)!=40)return 1;
 if(b[0]!=0x30||b[1]!=1||b[2]!=1||b[40]!=0xa5)return 2;
 for(unsigned i=3;i<34;i++)if(b[i])return 3;
 if(aux_master_leaf_encode(0x31,1,b,8)!=8||b[0]!=0x31||b[1]!=1)return 4;
 for(unsigned i=0;i<1024;i++)b[i]=0xa5;
 if(aux_master_leaf_encode(0x30,256,b,1024)!=-2)return 5;
 if(aux_master_leaf_encode(0x30,1,b,39)!=-4)return 6;
 for(unsigned i=0;i<1024;i++)if(b[i]!=0xa5)return 7;
 return 0;
}

#include <assert.h>
#include "master_route_setup.h"
struct mock_route {struct mr_setup *setup;unsigned sends,polls,bad_stage,mode;};
static int route_send(void *ctx,const uint8_t *p,size_t n) {
 struct mock_route *m=ctx;unsigned stage=m->sends++;
 assert(stage<2&&m->setup->tx[stage].commit_attempted==1);
 assert(m->setup->completed==stage);
 assert(p[0]==0x30+stage&&p[1]==1&&n==(stage?8u:40u));
 m->polls=0;
 return stage==m->bad_stage&&m->mode==1?-1:0;
}
static int route_recv(void *ctx,uint32_t *kind) {
 struct mock_route *m=ctx;unsigned stage=m->sends-1;m->polls++;
 assert(m->polls<=3);
 if(stage==m->bad_stage) {
  if(m->mode==2)return 0;
  if(m->mode==3){*kind=1;return 1;}
  if(m->mode==4)return -1;
 }
 if(m->polls<3)return 0;
 *kind=0x32;return 1;
}
int master_route_setup_test(void) {
 for(unsigned stage=0;stage<2;stage++)for(unsigned mode=0;mode<5;mode++) {
  struct mr_setup setup;mr_init_epoch(&setup);
  struct mock_route m={&setup,0,0,stage,mode};struct mr_io io={&m,route_send,route_recv};
  int result=mr_run_once(&setup,&io,3);
  const int expected[5]={MT_OK,MT_IO,MT_TIMEOUT,MT_UNEXPECTED,MT_PACKET};
  assert(result==expected[mode]);
  assert(m.sends==(mode?stage+1:2));
  assert(setup.completed==(mode?stage:2));
  unsigned sends=m.sends,polls=m.polls;
  assert(mr_run_once(&setup,&io,3)==MT_BUSY);
  assert(m.sends==sends&&m.polls==polls);
 }
 struct mr_setup s;mr_init_epoch(&s);assert(mr_run_once(&s,0,3)==MT_INVALID&&s.consumed==0);
 assert(mr_run_once(0,0,3)==MT_INVALID);mr_init_epoch(0);
 return 0;
}

struct wire_route {const uint8_t *ack;unsigned sends,polls,stage,mode;};
static int wire_send(void *ctx,const uint8_t *p,size_t n) {
 struct wire_route *m=ctx;assert(p[0]==0x30+m->sends&&n==(m->sends?8u:40u));m->sends++;return 0;
}
static int wire_recv(void *ctx,uint32_t *kind) {
 struct wire_route *m=ctx;uint8_t packet[9];for(unsigned i=0;i<8;i++)packet[i]=m->ack[i];packet[8]=0;
 size_t n=8;m->polls++;
 if(m->sends-1==m->stage) {
  if(m->mode==1)packet[7]^=1;
  if(m->mode==2)n=7;
  if(m->mode==3)n=9;
 }
 int result=aux_master_routing_ack_decode(packet,n);
 if(result<0)return -1;
 *kind=(uint32_t)result;return 1;
}
int master_route_wire_test(const uint8_t *ack,size_t length) {
 assert(length==8&&aux_master_routing_ack_decode(ack,length)==0x32);
 for(unsigned stage=0;stage<2;stage++)for(unsigned mode=0;mode<4;mode++) {
  struct mr_setup setup;mr_init_epoch(&setup);
  struct wire_route m={ack,0,0,stage,mode};struct mr_io io={&m,wire_send,wire_recv};
  assert(mr_run_once(&setup,&io,3)==(mode?MT_PACKET:MT_OK));
  assert(m.sends==(mode?stage+1:2));
  assert(mr_run_once(&setup,&io,3)==MT_BUSY);
 }
 /* Identical valid bytes accepted for both stages: duplicate identity cannot
  * be rejected without an external epoch/receive ownership contract. */
 return 0;
}
