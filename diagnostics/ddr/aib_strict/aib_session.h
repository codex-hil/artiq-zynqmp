/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef ARTIQ_AIB_SESSION_H
#define ARTIQ_AIB_SESSION_H
#include "aib_strict.h"
struct aib_session {uint64_t boot,nonce,sequence;unsigned armed,consumed;};
struct aib_receipt {
 uint64_t boot,nonce,sequence;
 unsigned accepted;
 struct aib_result result;
};
/* Local one-shot state only: trusted initialization/storage and serialized
 * execution required. Tokens are not authenticated hardware boot identity. */
int aib_session_arm(struct aib_session *,uint64_t boot,uint64_t nonce,uint64_t seq);
struct aib_receipt aib_session_execute(struct aib_session *,uint64_t boot,
 uint64_t nonce,uint64_t seq,const struct aib_io *,uint32_t mask,
 uint32_t poll_budget,uint64_t timeout_ticks);
#endif
