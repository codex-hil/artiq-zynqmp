/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_foreground_owner.h"
#include "master_aux_mmio.h"
/* Offline guarded/resumable replacement candidate for mm_bind ONLY.
 * Zero-initialize session and destination. Sole foreground owner, no ISR or
 * concurrent/reentrant bind/transport use. One profile read callback per step.
 * CSR identity values are compatibility checks, NOT actual map hash, live
 * clocks, hardware ownership, AXI fault containment or fresh epoch proof.
 */
enum mmb_error {MMB_INVALID=-50,MMB_IO=-51,MMB_PROFILE=-52,MMB_CANCELLED=-53,MMB_STALE=-54,MMB_BUSY=-55};
struct mmb_session {struct mfo_gate *gate;struct mm_transport *destination,candidate;uint64_t ticket,epoch;unsigned started,index;int terminal;};
static inline int mmb_same_owner(const struct mmb_session *s){
 return s&&s->started&&s->gate&&s->gate->owner==MFO_MASTER_OWNER&&s->gate->ticket==s->ticket&&s->gate->epoch==s->epoch;
}
static inline int mmb_fail(struct mmb_session *s,int error){
 if(!s||!s->started)return MMB_INVALID;
 if(s->terminal<0)return s->terminal;
 if(!mmb_same_owner(s)){s->terminal=MMB_STALE;return s->terminal;} /* Never touch another owner's destination. */
 if(s->gate->state==MFO_FAULT&&s->gate->error<0)error=s->gate->error;
 s->terminal=error<0?error:MMB_INVALID;s->destination->bound=0;s->destination->failed=1;
 mfo_fault(s->gate,s->terminal);return s->terminal;
}
/* Pure validation lets an enclosing owner validate before clearing its storage. */
static inline int mmb_validate(struct mfo_gate *g,uint64_t ticket,const struct mm_transport *destination,const struct mm_bus *bus,uint32_t budget){
 if(!g||!ticket||ticket!=g->ticket||g->state!=MFO_MASTER||g->owner!=MFO_MASTER_OWNER||!destination||destination->bound||destination->failed||destination->held||!bus||!bus->read||!bus->write||!bus->fence||!budget||budget>1024)return MMB_INVALID;
 if(g->profile_ticket==ticket||g->setup_ticket==ticket)return MMB_BUSY;
 return 0;
}
static inline int mmb_begin(struct mmb_session *s,struct mfo_gate *g,uint64_t ticket,struct mm_transport *destination,const struct mm_bus *bus,uint32_t budget){
 if(!s||s->started)return MMB_INVALID;
 int valid=mmb_validate(g,ticket,destination,bus,budget);if(valid)return valid;
 struct mm_bus bus_copy=*bus; /* May alias candidate.bus. */
 unsigned char *storage=(unsigned char *)s;
 for(size_t i=0;i<sizeof(*s);i++){storage[i]=0;}
 s->gate=g;s->destination=destination;s->candidate.bus=bus_copy;s->candidate.budget=budget;
 s->ticket=ticket;s->epoch=g->epoch;s->started=1;
 g->profile_ticket=ticket;return 0; /* Consume attempt before FIRST target read. */
}
static inline int mmb_cancel(struct mmb_session *s){return mmb_fail(s,MMB_CANCELLED);}
static inline int mmb_step(struct mmb_session *s){
 if(!s||!s->started)return MMB_INVALID;
 if(s->terminal<0)return s->terminal;
 if(!mmb_same_owner(s))return mmb_fail(s,MMB_STALE);
 if(s->gate->state==MFO_FAULT)return mmb_fail(s,s->gate->error);
 if(s->terminal==1)return 1;
 if(s->gate->state!=MFO_MASTER||s->gate->profile_ticket!=s->ticket||s->gate->setup_ticket==s->ticket||s->destination->bound||s->destination->failed||s->destination->held)return mmb_fail(s,MMB_BUSY);
 static const uint32_t address[3]={0xa0000800,0xa0000804,0xa0000808},expected[3]={0x47534d31,3,125000000};
 if(s->index>=3)return mmb_fail(s,MMB_INVALID);
 uint32_t value;int error=s->candidate.bus.read(s->candidate.bus.ctx,address[s->index],&value);
 if(s->terminal<0)return s->terminal; /* Synchronous cancel/fault wins. */
 if(!mmb_same_owner(s))return mmb_fail(s,MMB_STALE);
 if(s->gate->state==MFO_FAULT)return mmb_fail(s,s->gate->error);
 if(s->gate->state!=MFO_MASTER||s->gate->profile_ticket!=s->ticket||s->gate->setup_ticket==s->ticket)return mmb_fail(s,MMB_BUSY);
 if(error)return mmb_fail(s,MMB_IO);
 if(value!=expected[s->index])return mmb_fail(s,MMB_PROFILE);
 if(s->destination->bound||s->destination->failed||s->destination->held)return mmb_fail(s,MMB_BUSY);
 if(++s->index==3){s->candidate.bound=1;*s->destination=s->candidate;s->terminal=1;return 1;}
 return 0;
}
