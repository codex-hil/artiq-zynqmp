/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Unlinked target-compiler layout/frame probe; not a runtime allocation. */
#include "master_guarded_start.h"
unsigned char master_guarded_context_size[sizeof(struct mfg_start)];
__attribute__((noinline)) int master_guarded_probe_begin(struct mfg_start *s,struct mfo_gate *g,uint64_t ticket,const struct mm_bus *bus,uint32_t poll,uint32_t action,uint32_t route,uint32_t total){return mfg_begin(s,g,ticket,bus,poll,action,route,total);}
__attribute__((noinline)) int master_guarded_probe_step(struct mfg_start *s){return mfg_step(s);}
__attribute__((noinline)) int master_guarded_probe_cancel(struct mfg_start *s){return mfg_cancel(s);}
