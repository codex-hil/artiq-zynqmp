/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_setup_sequence.h"
static void advance(struct ms_setup *s,unsigned action){
 assert(ms_claim(s)==(int)action);assert(ms_claim(s)==-1);
 assert(ms_result(s,0)==0);assert(ms_result(s,1)==0);
}
int main(void){
 unsigned cases=0;struct ms_setup blank={0};assert(ms_claim(&blank)==-1);
 for(unsigned failstage=MS_LINK;failstage<=MS_BUFFER;failstage++)for(unsigned mode=0;mode<4;mode++){
  struct ms_setup s;assert(ms_init_epoch(&s,2,1)==0);
  for(unsigned a=MS_LINK;a<failstage;a++)advance(&s,a);
  assert(ms_claim(&s)==(int)failstage);
  if(mode==0)assert(ms_result(&s,-7)==-7);
  if(mode==1){assert(ms_result(&s,0)==0);assert(ms_result(&s,0)==-2);}
  if(mode==2)assert(ms_result(&s,2)==-3);
  if(mode==3)ms_link_lost(&s);
  assert(s.action==MS_FAILED&&ms_claim(&s)==-1&&ms_result(&s,1)==-1);
  assert(s.attempted==((1u<<(failstage+1))-2));cases++;
 }
 struct ms_setup s;assert(ms_init_epoch(&s,2,1)==0);
 assert(ms_result(&s,1)==-1&&s.action==MS_LINK);
 for(unsigned a=MS_LINK;a<=MS_BUFFER;a++)advance(&s,a);
 assert(s.action==MS_COMPLETE&&s.attempted==254&&ms_claim(&s)==-1);
 ms_link_lost(&s);assert(s.action==MS_FAILED);cases++;
 assert(ms_init_epoch(0,2,1)==-1);assert(ms_init_epoch(&s,0,1)==-1);
 assert(ms_init_epoch(&s,4097,1)==-1);assert(ms_init_epoch(&s,2,0)==-1);
 printf("MASTER_SETUP_SEQUENCE_PASS scenarios=%u actions=7\n",cases);return 0;
}
