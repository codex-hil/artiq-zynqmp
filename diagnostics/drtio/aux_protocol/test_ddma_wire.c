/* Real upstream Rust codec -> C service -> native reply/status; LGPL-3.0-or-later. */
#include <assert.h>
#include "ddma_service.h"
static unsigned starts;
static int start(void *context,const uint8_t *bytes,size_t n,uint64_t ts) {
 (void)context;assert(bytes[3]==0 && n==2048 && ts==8000000);starts++;return 0;
}
static void request(struct ddma_service *s,unsigned kind,struct ddma_packet *p,unsigned success) {
 uint8_t wire[1024];struct ddma_packet in,reply,decoded;
 int n=aux_ddma_encode(kind,p,wire,sizeof(wire));assert(n>0);
 assert(aux_ddma_decode(wire,n,&in)==(int)kind);
 unsigned response=ddma_service_request(s,kind,&in,&reply,1,start,0);
 assert(response==kind+1 && reply.succeeded==success);
 n=aux_ddma_encode(response,&reply,wire,sizeof(wire));assert(n>0);
 assert(aux_ddma_decode(wire,n,&decoded)==(int)response);
 assert(decoded.destination==p->source && decoded.succeeded==success);
}
int ddma_wire_test(void) {
 struct ddma_service s;struct ddma_packet p={0},status;
 ddma_service_init(&s);p.source=7;p.destination=1;p.id=42;p.timestamp=8000000;
 request(&s,0xb4,&p,0); /* incomplete */
 const uint8_t record[17]={17,0,0,1,8,0,0,0,0,0,0,0,0,1};
 p.status=1;p.length=5;memcpy(p.trace,record,5);request(&s,0xb0,&p,1);
 p.status=2;p.length=12;memcpy(p.trace,record+5,12);request(&s,0xb0,&p,1);
 request(&s,0xb4,&p,1);assert(starts==1);
 request(&s,0xb2,&p,0); /* active ownership */
 assert(!ddma_service_complete(&s,0,0,0));
 uint8_t wire[1024];int n=aux_ddma_encode(0xb6,&s.status,wire,sizeof(wire));assert(n>0);
 assert(aux_ddma_decode(wire,n,&status)==0xb6);
 assert(status.source==1 && status.destination==7 && status.id==42 && !status.error);
 wire[n-1]^=1;assert(aux_ddma_decode(wire,n,&status)==-1);
 request(&s,0xb4,&p,0); /* status must first be sent */
 assert(!ddma_service_status_sent(&s));request(&s,0xb2,&p,1);
 assert(!s.store.complete);return 0;
}
