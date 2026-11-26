/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_foreground_owner.h"
/* ISOLATED foreground policy only. Receipts and generation are supplied by a
 * separately qualified network/IRQ observer; this does not observe hardware.
 * Never call from ISR, concurrent callback or network error handler. A future
 * ISR publisher needs an independently reviewed synchronization protocol.
 * No GEM reset/recovery suppression, IRQ mask change or management callback.
 * Initialize storage once; no clearing/rebinding/recovery API. Check before
 * every master step AND publication. A fault during an in-flight callback is
 * not contained by this policy; nesting/AXI/panic gates remain independent.
 */
#define MNE_RECEIPTS 7u /* network health, IRQ/nesting contract, publication freshness */
enum mne_error {MNE_INVALID=-80,MNE_UNSAFE=-81,MNE_STALE=-82};
struct mne_policy {struct mfo_gate *gate;uint64_t ticket,epoch,generation;unsigned started;int error;};
static inline int mne_same_owner(const struct mne_policy *p){
 return p&&p->started&&p->gate&&p->gate->owner==MFO_MASTER_OWNER&&p->gate->ticket==p->ticket&&p->gate->epoch==p->epoch;
}
static inline int mne_fail(struct mne_policy *p){
 if(!p->error)p->error=mfo_fault(p->gate,MNE_UNSAFE);
 return p->error;
}
static inline int mne_observe(struct mne_policy *p,uint64_t generation,unsigned receipts,int fault){
 if(!p||!p->started)return MNE_INVALID;
 if(!mne_same_owner(p))return MNE_STALE; /* Never poison a newer owner's gate. */
 if(p->error)return p->error;
 if(p->gate->state==MFO_FAULT){p->error=p->gate->error<0?p->gate->error:MNE_UNSAFE;return p->error;}
 if((p->gate->state!=MFO_MASTER&&p->gate->state!=MFO_HELD)||!generation||generation!=p->generation||receipts!=MNE_RECEIPTS||fault)return mne_fail(p);
 return 0;
}
static inline int mne_begin(struct mne_policy *p,struct mfo_gate *g,uint64_t ticket,uint64_t generation,unsigned receipts,int fault){
 if(!p||p->started||!g||!ticket||!g->epoch||g->owner!=MFO_MASTER_OWNER||g->state!=MFO_MASTER||g->ticket!=ticket)return MNE_INVALID;
 p->gate=g;p->ticket=ticket;p->epoch=g->epoch;p->generation=generation;p->started=1;p->error=0;
 return mne_observe(p,generation,receipts,fault); /* Consume attempt before receipt validation. */
}
static inline int mne_ready(const struct mne_policy *p){
 return mne_same_owner(p)&&!p->error&&(p->gate->state==MFO_MASTER||p->gate->state==MFO_HELD);
}
