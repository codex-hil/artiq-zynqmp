/* Bounded direct-leaf DDMA upload staging; LGPL-3.0-or-later.
 * Pure memory policy: no MMIO, allocation, cache maintenance or playback.
 * PayloadStatus bits match pinned upstream: first=1, last=2.
 */
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#define DDMA_WINDOW 2048u
#define DDMA_PAYLOAD_MAX 1024u /*128B CDC FIFO + two read credits + drain headroom*/
struct ddma_store {
 uint8_t bytes[DDMA_WINDOW];
 uint32_t id;
 size_t length;
 uint8_t source, uploading, complete, rejected;
};
static inline void ddma_store_clear(struct ddma_store *s) { memset(s,0,sizeof(*s)); }
/* Retain only the rejected identity for idempotent cleanup. No payload or
 * playback permission survives. A new First fragment replaces this marker.
 */
static inline void ddma_store_invalidate(struct ddma_store *s) {
 uint32_t id=s->id;uint8_t source=s->source;
 ddma_store_clear(s);s->id=id;s->source=source;s->rejected=1;
}
/* Conservative first implementation: only 32-bit TTL writes on channels0/1,
 * destination1, fine3-aligned monotonic relative timestamps. Validate the
 * complete stream BEFORE stripping destination bytes. Upstream sends records
 * without terminator; the receiver adds terminator and speculative padding.
 */
static inline int ddma_store_validate(struct ddma_store *s) {
 uint64_t previous=0;
 for(size_t p=0;p<s->length;p+=17) {
  if(s->length-p<17 || s->bytes[p]!=17 || s->bytes[p+1]>1 ||
     s->bytes[p+2]!=0 || s->bytes[p+3]!=1) return -1;
  uint64_t timestamp=0;
  for(unsigned j=0;j<8;j++)timestamp|=(uint64_t)s->bytes[p+4+j]<<(8*j);
  if(timestamp>INT64_MAX || (timestamp&7) || (p && timestamp<previous))return -1;
  previous=timestamp;
  unsigned address=s->bytes[p+12];uint32_t value=0;
  for(unsigned j=0;j<4;j++)value|=(uint32_t)s->bytes[p+13+j]<<(8*j);
  if(s->bytes[p+1]==0 ? (address!=0 || value>1) : (address!=2 || value>3))return -1;
 }
 for(size_t p=0;p<s->length;p+=17)s->bytes[p+3]=0;
 memset(s->bytes+s->length,0,DDMA_WINDOW-s->length);
 return 0;
}
static inline int ddma_store_add(struct ddma_store *s,unsigned source,uint32_t id,
 unsigned status,const uint8_t *data,size_t length,unsigned busy) {
 if(busy || source>255 || status>3 || !data || !length)return -1;
 if(status&1) {ddma_store_clear(s);s->source=source;s->id=id;s->uploading=1;}
 if(!s->uploading || s->source!=source || s->id!=id)return -1;
 if(length>DDMA_PAYLOAD_MAX-s->length) {ddma_store_invalidate(s);return -1;}
 memcpy(s->bytes+s->length,data,length);s->length+=length;
 if(status&2) {
  s->uploading=0;
  if(ddma_store_validate(s)) {ddma_store_invalidate(s);return -1;}
  s->complete=1;
 }
 return 0;
}
static inline int ddma_store_remove(struct ddma_store *s,unsigned source,uint32_t id,unsigned busy) {
 if(busy || source>255 || s->source!=source || s->id!=id)return -1;
 if(s->rejected)return 0;
 if(!s->complete && !s->uploading)return -1;
 ddma_store_clear(s);return 0;
}
