/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Isolated target object, no main/startup/direct volatile MMIO. Not firmware. */
#include "master_aux_mmio.h"
#include "master_route_queue.h"
struct gm_aux_candidate {struct mm_transport mm;struct mq_transport queue;struct mr_setup route;};
int gm_aux_candidate_bind(struct gm_aux_candidate *c,const struct mm_bus *bus,uint32_t budget,int reviewed) {
 if(!c)return MT_INVALID;
 if(mm_bind(&c->mm,bus,budget,reviewed))return MT_INVALID;
 c->queue=(struct mq_transport){.rx={&c->mm,mm_acquire,mm_release},.ctx=&c->mm,.pending=mm_pending,.send=mm_send};
 mr_init_epoch(&c->route);return MT_OK;
}
int gm_aux_candidate_route_once(struct gm_aux_candidate *c,uint32_t budget) {
 if(!c)return MT_INVALID;
 return mq_route_once(&c->route,&c->queue,budget);
}
