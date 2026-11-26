/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "master_network_fault_observer.h"
void mnf_probe_publish(struct mnf_latch *latch){mnf_publish(latch);}
unsigned mnf_probe_seen(const struct mnf_latch *latch){return mnf_seen(latch);}
int mnf_probe_observe(void *ctx,struct mnh_health *out){return mnf_observe(ctx,out);}
