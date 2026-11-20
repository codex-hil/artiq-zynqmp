/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_foreground_owner.h"
/* Offline command-class policy ONLY. No mailbox access or firmware integration.
 * Single foreground owner. Every NEW_WORK dispatch must reserve via this gate;
 * an existing worker may finish RPC/recovery while a master request drains it.
 * Event qualification is external: current mailbox has no echoed ownership
 * ticket. These software tokens/event IDs do NOT establish wire correlation.
 */
enum mwp_phase {MWP_ASYNC_REPLY=1,MWP_SYNC_REPLY,MWP_EXCEPTION_ACK};
struct mwp_reply {uint64_t ticket,epoch,event;enum mwp_phase phase;unsigned armed,attempted;};
static inline int mwp_current(const struct mfo_gate *g,uint64_t ticket,uint64_t epoch){
 return g&&ticket&&epoch==g->epoch&&ticket==g->ticket&&g->owner==MFO_WORKER_OWNER&&
  (g->state==MFO_WORKER||g->state==MFO_DRAINING);
}
static inline int mwp_new_work(struct mfo_gate *g,unsigned command){
 if(command!=1&&command!=2)return MFO_INVALID;
 return mfo_worker_dispatch(g); /* Record reservation before external command. */
}
static inline int mwp_arm(struct mwp_reply *r,const struct mfo_gate *g,uint64_t ticket,
 uint64_t epoch,uint64_t event,enum mwp_phase phase,unsigned qualified_event){
 if(!r||!mwp_current(g,ticket,epoch)||qualified_event!=1||!event||event<=r->event||
  phase<MWP_ASYNC_REPLY||phase>MWP_EXCEPTION_ACK)return MFO_INVALID;
 if(r->armed&&!r->attempted&&r->ticket==ticket&&r->epoch==epoch)return MFO_BUSY; /* Do not replace outstanding reply. */
 *r=(struct mwp_reply){.ticket=ticket,.epoch=epoch,.event=event,.phase=phase,.armed=1};return 0;
}
static inline int mwp_progress_once(struct mwp_reply *r,const struct mfo_gate *g,unsigned command){
 if(!r||!r->armed||r->attempted||!mwp_current(g,r->ticket,r->epoch))return MFO_INVALID;
 int allowed=(r->phase==MWP_ASYNC_REPLY&&command==3)||
  (r->phase==MWP_SYNC_REPLY&&(command==4||command==7))||
  (r->phase==MWP_EXCEPTION_ACK&&command==6);
 if(!allowed)return MFO_INVALID;
 r->attempted=1;return 0; /* Mark BEFORE publication; failure must not retry. */
}
/* Caller latches this before abandoned/failed command publication. No stop ACK,
 * task preemption, quiescence, ticket release or automatic master grant. */
static inline int mwp_abandon(struct mfo_gate *g,uint64_t ticket,uint64_t epoch,int error){
 if(!mwp_current(g,ticket,epoch))return MFO_INVALID;
 return mfo_fault(g,error);
}
