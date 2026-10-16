/* Native host policy tests, no hardware; LGPL-3.0-or-later. */
#include <assert.h>
#include <stdio.h>
#include "ddma_store.h"
int main(void) {
 struct ddma_store s;uint8_t r[34]={17,0,0,1,8,0,0,0,0,0,0,0,0,1};
 memcpy(r+17,r,17);r[21]=16;
 ddma_store_clear(&s);
 assert(ddma_store_add(&s,0,42,0,r,17,0)<0); /* no first */
 assert(ddma_store_add(&s,0,42,1,r,5,0)==0);
 assert(ddma_store_add(&s,1,42,2,r+5,29,0)<0); /* source mismatch */
 assert(ddma_store_add(&s,0,43,2,r+5,29,0)<0); /* ID mismatch */
 assert(ddma_store_add(&s,0,42,2,r+5,29,0)==0);
 assert(s.complete && s.length==34 && s.bytes[3]==0 && s.bytes[20]==0);
 for(unsigned i=34;i<DDMA_WINDOW;i++)assert(s.bytes[i]==0);
 assert(ddma_store_remove(&s,0,42,1)<0 && s.complete);
 assert(ddma_store_add(&s,0,42,3,r,34,1)<0 && s.complete);
 assert(ddma_store_remove(&s,0,43,0)<0 && s.complete);
 assert(ddma_store_remove(&s,0,42,0)==0 && !s.complete);
 for(unsigned i=0;i<34;i++) { /* every truncated final length */
  if(i==17)continue;
  assert(ddma_store_add(&s,0,42,3,r,i,0)<0 && !s.complete);
 }
 unsigned offsets[]={0,1,2,3,4,11,12,13,16};
 for(unsigned i=0;i<sizeof(offsets)/sizeof(*offsets);i++) {
  uint8_t bad[34];memcpy(bad,r,34);bad[offsets[i]]=255;
  assert(ddma_store_add(&s,0,42,3,bad,34,0)<0 && !s.complete);
 }
 r[21]=0;assert(ddma_store_add(&s,0,42,3,r,34,0)<0);r[21]=16;
 uint8_t large[DDMA_PAYLOAD_MAX];memset(large,0,sizeof(large));
 assert(ddma_store_add(&s,0,42,1,large,sizeof(large),0)==0);
 assert(ddma_store_add(&s,0,42,2,r,1,0)<0 && !s.uploading);
 assert(ddma_store_add(&s,0,42,3,r,34,0)==0); /* recovery */
 uint8_t maximum[17*90];
 for(unsigned i=0;i<90;i++)memcpy(maximum+17*i,r,17);
 assert(ddma_store_add(&s,255,0xffffffff,3,maximum,sizeof(maximum),0)==0);
 assert(s.complete && s.length==1530 && s.bytes[1530]==0);
 assert(ddma_store_add(&s,256,42,3,r,34,0)<0 && s.complete);
 assert(ddma_store_add(&s,0,42,4,r,34,0)<0 && s.complete);
 puts("DDMA_STORE_OFFLINE_PASS fragmented, bounds, records, ownership, busy, recovery");
}
