/* Bad upload cannot reach mock hardware; LGPL-3.0-or-later. */
#include <assert.h>
#include <stdio.h>
#include "ddma_service.h"
static unsigned starts;
static int start(void *c,const uint8_t *bytes,size_t length,uint64_t timestamp) {
 (void)c;assert(length==2048 && bytes[3]==0 && timestamp==8000000);starts++;return 0;
}
static void add(struct ddma_service *s,struct ddma_packet *p,unsigned success) {
 struct ddma_packet reply;
 assert(ddma_service_request(s,0xb0,p,&reply,1,start,0)==0xb1);
 assert(reply.succeeded==success);
}
static void playback(struct ddma_service *s,struct ddma_packet *p,unsigned success) {
 struct ddma_packet reply;
 assert(ddma_service_request(s,0xb4,p,&reply,1,start,0)==0xb5);
 assert(reply.succeeded==success);
}
int main(void) {
 struct ddma_service s;struct ddma_packet p={0};
 const uint8_t record[17]={17,0,0,1,8,0,0,0,0,0,0,0,0,1};
 ddma_service_init(&s);p.destination=1;p.id=42;p.timestamp=8000000;
 p.status=2;p.length=17;memcpy(p.trace,record,17);add(&s,&p,0);playback(&s,&p,0);
 p.status=1;p.length=16;add(&s,&p,1);playback(&s,&p,0);
 p.status=2;p.source=1;p.length=1;add(&s,&p,0);p.source=0;
 p.status=3;p.length=16;add(&s,&p,0);playback(&s,&p,0); /* final truncated */
 p.length=17;p.trace[0]=16;add(&s,&p,0);playback(&s,&p,0);p.trace[0]=17;
 p.trace[3]=2;add(&s,&p,0);playback(&s,&p,0);p.trace[3]=1;
 p.status=1;p.length=1010;memset(p.trace,0,sizeof(p.trace));add(&s,&p,1);
 p.status=2;p.length=15;add(&s,&p,0);playback(&s,&p,0); /*1025 > policy*/
 p.status=3;p.length=1011;add(&s,&p,0);playback(&s,&p,0); /*larger than wire array*/
 p.length=17;p.status=4;add(&s,&p,0);playback(&s,&p,0);
 assert(starts==0 && !s.running && !s.store.complete);
 /* A fresh valid first/last upload must recover after each rejection chain. */
 p.status=3;memcpy(p.trace,record,17);add(&s,&p,1);playback(&s,&p,1);
 assert(starts==1 && s.running);
 add(&s,&p,0);assert(s.store.complete); /* busy cannot corrupt active slot */
 assert(!ddma_service_complete(&s,0,0,0));playback(&s,&p,0);
 assert(!ddma_service_status_sent(&s));playback(&s,&p,1);assert(starts==2);
 puts("DDMA_REJECT_OFFLINE_PASS zero starts for invalid uploads; valid recovery and busy ownership");
}
