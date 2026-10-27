/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef ARTIQ_AIB_BACKEND_H
#define ARTIQ_AIB_BACKEND_H
#include "aib_strict.h"
struct aib_transport {
 void *ctx;
 int (*read32)(void *,uint32_t,uint32_t *);
 int (*write32)(void *,uint32_t,uint32_t);
 int (*ticks)(void *,uint64_t *);
};
struct aib_backend {
 struct aib_transport transport;
 struct aib_io io;
 uint32_t mask,initial_request,initial_type;
 unsigned sealed,ready,write_attempted;
};
/* Policy adapter only. No volatile/MMIO implementation, hardware deployment or
 * trust in caller state is supplied. Zero-init and exclusive ownership required. */
int aib_backend_prepare(struct aib_backend *,const struct aib_transport *,uint32_t mask);
#endif
