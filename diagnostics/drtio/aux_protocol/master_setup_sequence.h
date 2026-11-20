/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include <stdint.h>
/* Host-only setup planner. These actions describe backend obligations, NOT
 * AUX packet kinds. In particular SET_TIME is RT CSR trigger+completion and
 * TSC_ACK is spontaneous satellite response. ROUTING means reviewed table+rank,
 * not merely one successful fixed-leaf packet. No transport or MMIO here.
 * Each action claimed once before external operation; no retries/reinit.
 * Backend must report qualified completion, not fabricate success. Counts are
 * caller steps, not physical time. Completion grants no deployed capability.
 */
enum ms_action {MS_LINK=1,MS_ECHO,MS_SET_TIME,MS_TSC_ACK,MS_ROUTING,MS_STATUS,MS_BUFFER,MS_COMPLETE,MS_FAILED};
struct ms_setup {enum ms_action action;uint32_t budget,left,attempted;unsigned issued;int error;};
static inline int ms_init_epoch(struct ms_setup *s,uint32_t budget,int qualified_epoch){
 if(!s||!budget||budget>4096||qualified_epoch!=1)return -1;
 *s=(struct ms_setup){.action=MS_LINK,.budget=budget,.left=budget};return 0;
}
static inline int ms_claim(struct ms_setup *s){
 if(!s||s->issued||s->action<MS_LINK||s->action>=MS_COMPLETE)return -1;
 s->issued=1;s->attempted|=1u<<s->action;return (int)s->action;
}
/* pending0, qualified_success1, backend_error<0. Unexpected positive refused.
 * A success at last poll unit is accepted; unknown outcomes never replayed.
 */
static inline int ms_result(struct ms_setup *s,int result){
 if(!s||!s->issued||s->action<MS_LINK||s->action>=MS_COMPLETE)return -1;
 if(result==1){s->action=(enum ms_action)(s->action+1);s->issued=0;s->left=s->budget;return 0;}
 if(result==0&&--s->left)return 0;
 s->error=result<0?result:result==0?-2:-3;s->action=MS_FAILED;return s->error;
}
static inline void ms_link_lost(struct ms_setup *s){
 if(s){s->error=-4;s->action=MS_FAILED;}
}
