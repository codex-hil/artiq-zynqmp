/* Dispatcher policy tests, mocked hardware admission; LGPL-3.0-or-later. */
#include <assert.h>
#include <stdio.h>
#include "ddma_service.h"
struct backend {unsigned calls;int fail;};
static int start(void *context,const uint8_t *bytes,size_t size,uint64_t ts) {
 struct backend *b=context;b->calls++;
 assert(size==2048 && bytes[3]==0 && bytes[17]==0 && ts==8000);
 return b->fail;
}
/* Exercise completion ownership and fail-closed admission for every native
 * CRI status. Backend readiness is deliberately latched low after a fault,
 * matching ddma_poll/ddma_ready; this is a policy test, not a hardware fault.
 */
static void completion_fault_lifecycle(void) {
 for(unsigned raw=0;raw<=12;raw+=4) {
  struct ddma_service s;struct ddma_packet p={0},r;struct backend b={0,0};
  ddma_service_init(&s);
  p.source=7;p.destination=1;p.id=0xabc;p.timestamp=8000;
  p.status=3;p.length=17;p.trace[0]=17;p.trace[3]=1;
  p.trace[4]=8;p.trace[13]=1;
  assert(ddma_service_request(&s,0xb0,&p,&r,1,start,&b)==0xb1 && r.succeeded);
  assert(ddma_service_request(&s,0xb4,&p,&r,1,start,&b)==0xb5 && r.succeeded);
  unsigned mapped=(unsigned)ddma_aux_error(raw);
  assert(!ddma_service_complete(&s,mapped,0x10001,0x123456789ull));
  assert(!s.running && s.status_pending);
  assert(s.status.source==1 && s.status.destination==7 && s.status.id==p.id);
  assert(s.status.error==mapped && s.status.channel==0x10001 &&
         s.status.timestamp==0x123456789ull);
  /* No reuse or erase until the transport has sent the status. */
  ddma_service_request(&s,0xb4,&p,&r,1,start,&b);assert(!r.succeeded && b.calls==1);
  ddma_service_request(&s,0xb2,&p,&r,1,start,&b);assert(!r.succeeded);
  assert(!ddma_service_status_sent(&s));
  unsigned ready=raw==0;
  ddma_service_request(&s,0xb4,&p,&r,ready,start,&b);
  assert(r.succeeded==ready && b.calls==1+ready);
  if(ready) {
   assert(!ddma_service_complete(&s,0,0,0));
   assert(!ddma_service_status_sent(&s));
  }
  /* Faulted readiness still permits explicit idle-slot cleanup. */
  ddma_service_request(&s,0xb2,&p,&r,0,start,&b);
  assert(r.succeeded && !s.store.complete);
 }
}
int main(void) {
 completion_fault_lifecycle();
 for(unsigned raw=0;raw<256;raw++) {
  int mapped=ddma_aux_error(raw);
  if(raw & ~12u)assert(mapped==-1);
  else assert(mapped==(int)(raw/4));
 }
 assert(ddma_aux_error(256)==-1); /* reject unknown future CSR bits too */
 struct ddma_service s;struct ddma_packet p={0},r;struct backend b={0,0};
 ddma_service_init(&s);p.destination=1;p.id=42;p.timestamp=8000;
 assert(ddma_service_request(&s,0xb4,&p,&r,1,start,&b)==0xb5 && !r.succeeded && !b.calls);
 p.status=3;p.length=17;p.trace[0]=17;p.trace[3]=1;p.trace[4]=8;p.trace[13]=1;
 assert(ddma_service_request(&s,0xb0,&p,&r,0,start,&b)==0xb1 && !r.succeeded);
 p.destination=2;assert(!ddma_service_request(&s,0xb0,&p,&r,1,start,&b));p.destination=1;
 assert(ddma_service_request(&s,0xb0,&p,&r,1,start,&b)==0xb1 && r.succeeded && r.source==1 && r.destination==0 && r.id==42);
 p.timestamp=INT64_MAX-7;
 ddma_service_request(&s,0xb4,&p,&r,1,start,&b);assert(!r.succeeded && !b.calls);
 p.timestamp=8000;
 b.fail=1;ddma_service_request(&s,0xb4,&p,&r,1,start,&b);assert(!r.succeeded && !s.running);
 b.fail=0;p.timestamp=8001;ddma_service_request(&s,0xb4,&p,&r,1,start,&b);assert(!r.succeeded && b.calls==1);p.timestamp=8000;
 p.id=43;ddma_service_request(&s,0xb4,&p,&r,1,start,&b);assert(!r.succeeded);p.id=42;
 ddma_service_request(&s,0xb4,&p,&r,1,start,&b);assert(r.succeeded && s.running && b.calls==2);
 ddma_service_request(&s,0xb2,&p,&r,1,start,&b);assert(!r.succeeded && s.store.complete);
 ddma_service_request(&s,0xb4,&p,&r,1,start,&b);assert(!r.succeeded && b.calls==2);
 assert(!ddma_service_complete(&s,65,3,1234));assert(s.status_pending && s.status.error==65 && s.status.id==42 && s.status.destination==0);
 assert(ddma_service_complete(&s,0,0,0)<0);
 ddma_service_request(&s,0xb0,&p,&r,1,start,&b);assert(!r.succeeded);
 assert(!ddma_service_status_sent(&s));assert(ddma_service_status_sent(&s)<0);
 ddma_service_request(&s,0xb4,&p,&r,1,start,&b);assert(r.succeeded && b.calls==3);
 assert(!ddma_service_complete(&s,0,0,0));assert(!ddma_service_status_sent(&s));
 ddma_service_request(&s,0xb2,&p,&r,0,start,&b);assert(r.succeeded && !s.store.complete);
 puts("DDMA_SERVICE_OFFLINE_PASS upload, admission, busy, status, recovery");
}
