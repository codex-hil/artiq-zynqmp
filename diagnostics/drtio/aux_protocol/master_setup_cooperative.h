/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_setup_sequence.h"
#include "master_star_step.h"
/* Host-only whole-setup coordinator. One backend action callback OR one route
 * step per foreground turn. Nonrouting callback receives start1 once, then0;
 * returns0 pending,1 qualified candidate completion,negative error. It MUST NOT
 * reissue external operations on pending calls. No wall-time/AXI-hang bound.
 * Single foreground owner, no concurrent or recursive step/init calls. Callbacks
 * may request cancellation synchronously; cancellation wins over their result.
 * Initialize only after externally qualified fresh epoch, never to clear failure.
 * Routing has its own per-request budget, not the short phase budget.
 */
struct msc_io {void *ctx;int (*action_step)(void *,enum ms_action,unsigned);struct mr_io route;};
struct msc_setup {struct ms_setup plan;struct msi_table route;uint32_t routing_turns_left;unsigned initialized;};
static inline int msc_init_epoch(struct msc_setup *s,uint32_t action_budget,uint32_t route_budget,int reviewed_epoch){
 if(!s||!action_budget||action_budget>4096||!route_budget||route_budget>4096||reviewed_epoch!=1)return MT_INVALID;
 *s=(struct msc_setup){.routing_turns_left=257*(route_budget+1),.initialized=1};
 ms_init_epoch(&s->plan,action_budget,1);msi_init_epoch(&s->route,route_budget,1);return 0;
}
static inline int msc_step(struct msc_setup *s,const struct msc_io *io){
 if(!s||!s->initialized||!io||!io->action_step||!io->route.send||!io->route.recv)return MT_INVALID;
 if(s->plan.action==MS_COMPLETE)return 1;
 if(s->plan.action==MS_FAILED)return s->plan.error;
 unsigned start=!s->plan.issued;
 if(start&&ms_claim(&s->plan)<0)return MT_INVALID;
 int result;
 if(s->plan.action==MS_ROUTING){
  if(!s->routing_turns_left)result=MT_TIMEOUT;
  else {s->routing_turns_left--;result=msi_step(&s->route,&io->route);}
  if(result==0&&s->routing_turns_left)return 0;
  if(result==0)result=MT_TIMEOUT;
 }else result=io->action_step(io->ctx,s->plan.action,start);
 if(s->plan.action==MS_FAILED)return s->plan.error;
 int error=ms_result(&s->plan,result);
 if(error){if(!s->route.terminal)msi_cancel(&s->route);return error;}
 return s->plan.action==MS_COMPLETE?1:0;
}
/* Cancellation never clears/drains/retries a transport or undoes an attempted
 * commit. Caller separately withdraws admission and qualifies reset/abandonment. */
static inline void msc_cancel(struct msc_setup *s){
 if(s&&s->initialized&&s->plan.action!=MS_FAILED){s->plan.action=MS_FAILED;s->plan.error=-100;if(!s->route.terminal)msi_cancel(&s->route);}
}
