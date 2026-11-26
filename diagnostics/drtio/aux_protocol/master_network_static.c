/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "master_network_static.h"
_Alignas(64) static struct mnh_start mns_context;
int mns_begin(struct mfo_gate *gate,uint64_t ticket,const struct mm_bus *bus,void *ctx,mnh_observer observer,uint32_t poll,uint32_t action,uint32_t route,uint32_t total){
 return mnh_begin(&mns_context,gate,ticket,bus,ctx,observer,poll,action,route,total);
}
int mns_poll(void){return mnh_step(&mns_context);}
int mns_snapshot(struct mnh_status *out){return mnh_snapshot(&mns_context,out);}
