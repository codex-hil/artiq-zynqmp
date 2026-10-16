/* Direct-leaf DDMA dispatcher, no transport/MMIO; LGPL-3.0-or-later. */
#pragma once
#include "ddma_codec.h"
#include "ddma_store.h"
/* Lab CSR bits are not the upstream AUX status ABI. Only native CRI faults
 * have a corresponding upstream status (underflow=1, unreachable=2).
 * Internal faults must terminate the session instead of sending a misleading
 * status: the current upstream master ignores other error bits.
 */
static inline int ddma_aux_error(unsigned raw) {
 return (raw & ~12u) ? -1 : (int)(raw >> 2);
}
struct ddma_service {
 struct ddma_store store;
 unsigned running, status_pending;
 struct ddma_packet status;
};
/* Backend must copy/flush the full padded window, validate readiness and future
 * timestamp, then report successful CSR admission. It must not replay events
 * in software. Return nonzero on failure; do not start hardware on failure.
 */
typedef int (*ddma_start_fn)(void *,const uint8_t *,size_t,uint64_t);
static inline void ddma_service_init(struct ddma_service *s) {memset(s,0,sizeof(*s));}
/* Returns reply opcode; 0 means unhandled/wrong destination, no mutation.
 * Caller must send the reply or fail closed; transport loss after successful
 * admission cannot undo already accepted RTIO output.
 */
static inline unsigned ddma_service_request(struct ddma_service *s,unsigned kind,
 const struct ddma_packet *p,struct ddma_packet *reply,unsigned ready,
 ddma_start_fn start,void *context) {
 if(p->destination!=1 || p->source>255 ||
    (kind!=0xb0 && kind!=0xb2 && kind!=0xb4))return 0;
 memset(reply,0,sizeof(*reply));reply->source=1;reply->destination=p->source;reply->id=p->id;
 unsigned busy=s->running || s->status_pending;int result=-1;
 if(kind==0xb0) {
  if(ready && p->length<=sizeof(p->trace))
   result=ddma_store_add(&s->store,p->source,p->id,p->status,p->trace,p->length,busy);
 } else if(kind==0xb2) {
  result=ddma_store_remove(&s->store,p->source,p->id,busy);
 } else if(ready && !busy && s->store.complete && s->store.source==p->source &&
           s->store.id==p->id && p->timestamp && p->timestamp<=INT64_MAX &&
           !(p->timestamp&7) && start) {
  uint64_t last=0;size_t base=s->store.length-17;
  for(unsigned j=0;j<8;j++)last|=(uint64_t)s->store.bytes[base+4+j]<<(8*j);
  if(last<=INT64_MAX-p->timestamp)
   result=start(context,s->store.bytes,DDMA_WINDOW,p->timestamp);
  if(!result) {
   s->running=1;memset(&s->status,0,sizeof(s->status));
   s->status.source=1;s->status.destination=p->source;s->status.id=p->id;
  }
 }
 reply->succeeded=result==0;
 return kind+1;
}
/* Engine completion is admission/drain completion, not elapsed event time.
 * Do not release ownership on completion until status transport succeeds.
 */
static inline int ddma_service_complete(struct ddma_service *s,unsigned error,
 uint32_t channel,uint64_t timestamp) {
 if(!s->running || error>255)return -1;
 s->running=0;s->status_pending=1;
 s->status.error=error;s->status.channel=channel;s->status.timestamp=timestamp;
 return 0;
}
static inline int ddma_service_status_sent(struct ddma_service *s) {
 if(!s->status_pending)return -1;
 s->status_pending=0;return 0;
}
