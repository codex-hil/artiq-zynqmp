/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include <stdint.h>
/* Offline policy model ONLY, not a hardware lease or worker handshake.
 * Sole CPU0 foreground owner; every worker dispatch must use this arbiter.
 * Never call from ISR/concurrent/reentrant callbacks. Receipt flags represent
 * external obligations, not detection. No MMIO, reset or automatic recovery.
 * Initialize once at boot; never reinitialize to clear an outstanding owner.
 */
enum mfo_state {MFO_CLOSED,MFO_IDLE,MFO_WORKER,MFO_DRAINING,MFO_WAIT_MASTER,
 MFO_MASTER,MFO_HELD,MFO_FAULT};
enum mfo_owner {MFO_NONE,MFO_WORKER_OWNER,MFO_MASTER_OWNER};
enum mfo_error {MFO_INVALID=-1,MFO_BUSY=-2,MFO_CANCELLED=-3};
struct mfo_gate {enum mfo_state state;enum mfo_owner owner;uint64_t epoch,serial,ticket,setup_ticket;int error;};
#define MFO_FRESH_RECEIPTS 15u /* map/clock epoch, all requesters quiet, AUX exclusive, outcomes reconciled */
#define MFO_MASTER_RECEIPTS 7u /* worker quiescence, CRI exclusive, AUX exclusive */
#define MFO_RELEASE_RECEIPTS 7u /* no pending operation, CRI unforced, AUX no borrowed/pending response */
static inline void mfo_init(struct mfo_gate *g){if(g)*g=(struct mfo_gate){0};}
static inline int mfo_fault(struct mfo_gate *g,int error){
 if(!g)return MFO_INVALID;
 if(g->state!=MFO_FAULT){g->state=MFO_FAULT;g->error=error<0?error:MFO_INVALID;}
 return g->error; /* Preserve owner/ticket and original error, no release. */
}
static inline int mfo_fresh_epoch(struct mfo_gate *g,uint64_t epoch,unsigned receipts){
 if(!g||!epoch||epoch<=g->epoch||receipts!=MFO_FRESH_RECEIPTS)return MFO_INVALID;
 if(g->state!=MFO_CLOSED&&g->state!=MFO_FAULT)return MFO_BUSY;
 g->epoch=epoch;g->state=MFO_IDLE;g->owner=MFO_NONE;g->ticket=0;g->error=0;return 0;
}
static inline int mfo_new_ticket(struct mfo_gate *g,enum mfo_owner owner){
 if(g->serial==UINT64_MAX)return mfo_fault(g,MFO_INVALID); /* Never wrap/alias stale ticket. */
 g->ticket=++g->serial;g->owner=owner;return 0;
}
static inline int mfo_worker_dispatch(struct mfo_gate *g){
 if(!g)return MFO_INVALID;
 if(g->state!=MFO_IDLE)return MFO_BUSY;
 int r=mfo_new_ticket(g,MFO_WORKER_OWNER);if(r)return r;
 g->state=MFO_WORKER;return 0; /* Mark owner BEFORE external worker command. */
}
static inline int mfo_request_master(struct mfo_gate *g){
 if(!g)return MFO_INVALID;
 if(g->state==MFO_IDLE){g->state=MFO_WAIT_MASTER;return 0;}
 if(g->state==MFO_WORKER){g->state=MFO_DRAINING;return 0;}
 return MFO_BUSY; /* Never dispatch a stop/reset command here. */
}
static inline int mfo_worker_quiesced(struct mfo_gate *g,uint64_t ticket,unsigned receipt){
 if(!g||!ticket||ticket!=g->ticket||g->owner!=MFO_WORKER_OWNER||receipt!=1)return MFO_INVALID;
 if(g->state!=MFO_WORKER&&g->state!=MFO_DRAINING)return MFO_BUSY;
 g->state=g->state==MFO_DRAINING?MFO_WAIT_MASTER:MFO_IDLE;
 g->owner=MFO_NONE;g->ticket=0;return 0;
}
static inline int mfo_grant_master(struct mfo_gate *g,unsigned receipts){
 if(!g||receipts!=MFO_MASTER_RECEIPTS)return MFO_INVALID;
 if(g->state!=MFO_WAIT_MASTER||g->owner!=MFO_NONE)return MFO_BUSY;
 int r=mfo_new_ticket(g,MFO_MASTER_OWNER);if(r)return r;
 g->state=MFO_MASTER;return 0; /* Must precede mm_bind and any target read. */
}
static inline int mfo_setup_result(struct mfo_gate *g,uint64_t ticket,int result){
 if(!g||!ticket||ticket!=g->ticket||g->owner!=MFO_MASTER_OWNER)return MFO_INVALID;
 if(g->state==MFO_FAULT)return g->error;
 if(g->state!=MFO_MASTER)return MFO_BUSY;
 if(result<0)return mfo_fault(g,result);
 if(result>1)return mfo_fault(g,MFO_INVALID);
 if(result==1)g->state=MFO_HELD; /* Success retains reservation; not admission. */
 return 0;
}
static inline int mfo_release_master(struct mfo_gate *g,uint64_t ticket,unsigned receipts){
 if(!g||!ticket||ticket!=g->ticket||g->owner!=MFO_MASTER_OWNER||receipts!=MFO_RELEASE_RECEIPTS)return MFO_INVALID;
 if(g->state!=MFO_HELD)return MFO_BUSY;
 g->state=MFO_IDLE;g->owner=MFO_NONE;g->ticket=0;return 0;
}
