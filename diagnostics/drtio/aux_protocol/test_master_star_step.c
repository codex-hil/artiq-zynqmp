/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_star_step.h"
struct step_mock {struct msi_table *s;unsigned stage,mode,sends,receives,polls;};
static int step_send(void *ctx,const uint8_t *p,size_t n){
 struct step_mock *m=ctx;unsigned stage=m->sends++;assert(stage==m->s->completed&&m->s->tx.commit_attempted);
 assert(p[0]==(stage<256?0x30:0x31)&&n==(stage<256?40u:8u));
 if(stage<256){assert(p[1]==stage);for(unsigned i=0;i<32;i++){unsigned v=0xff;if(stage==0&&i==0)v=0;if(stage==1&&i==0)v=1;if(stage==1&&i==1)v=0;assert(p[2+i]==v);}}
 else assert(p[1]==1);
 m->polls=0;return stage==m->stage&&m->mode==1?-1:0;
}
static int step_recv(void *ctx,uint32_t *kind){
 struct step_mock *m=ctx;m->receives++;m->polls++;assert(m->polls<=3);
 if(m->sends-1==m->stage){if(m->mode==2)return 0;if(m->mode==3){*kind=1;return 1;}if(m->mode==4)return -1;}
 if(m->polls<3)return 0;
 *kind=0x32;return 1;
}
static void exercise(unsigned stage,unsigned mode){
 struct msi_table s;assert(msi_init_epoch(&s,3,1)==0);struct step_mock m={&s,stage,mode,0,0,0};struct mr_io io={&m,step_send,step_recv};
 unsigned iterations=0;int r=0;
 while(!r){unsigned calls=m.sends+m.receives;r=msi_step(&s,&io);assert(m.sends+m.receives-calls<=1);assert(++iterations<=1028);}
 const int expected[5]={1,MT_IO,MT_TIMEOUT,MT_UNEXPECTED,MT_PACKET};assert(r==expected[mode]);
 assert(s.completed==(mode?stage:257)&&m.sends==(mode?stage+1:257)&&s.send_attempts==m.sends);
 if(!mode)assert(iterations==1028);
 unsigned calls=m.sends+m.receives;assert(msi_step(&s,&io)==r&&m.sends+m.receives==calls);
}
int master_star_step_test(void){
 exercise(0,0);unsigned cases=1;
 for(unsigned stage=0;stage<257;stage++)for(unsigned mode=1;mode<=4;mode++){exercise(stage,mode);cases++;}
 struct msi_table s;assert(msi_init_epoch(&s,3,1)==0);struct step_mock m={&s,0,0,0,0,0};struct mr_io io={&m,step_send,step_recv};
 assert(msi_step(&s,&io)==0&&m.sends==1);msi_cancel(&s);assert(msi_step(&s,&io)==MT_IO&&m.receives==0&&s.tx.commit_attempted==1);
 assert(msi_init_epoch(&s,3,0)==MT_INVALID);assert(msi_init_epoch(&s,0,1)==MT_INVALID);
 printf("MASTER_STAR_STEP_PASS scenarios=%u one_transport_callback_per_step\n",cases);return 0;
}
