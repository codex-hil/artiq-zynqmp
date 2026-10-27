/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "aib_session.h"
int aib_session_arm(struct aib_session *s,uint64_t boot,uint64_t nonce,uint64_t seq) {
 if(!s || s->armed || s->consumed || !boot || !nonce || !seq)return -1;
 s->boot=boot;s->nonce=nonce;s->sequence=seq;s->armed=1;return 0;
}
struct aib_receipt aib_session_execute(struct aib_session *s,uint64_t boot,
 uint64_t nonce,uint64_t seq,const struct aib_io *io,uint32_t mask,
 uint32_t budget,uint64_t timeout) {
 struct aib_receipt r={0};r.boot=boot;r.nonce=nonce;r.sequence=seq;
 r.result.status=AIB_REJECTED;
 if(!s || !s->armed || s->consumed || s->boot!=boot || s->nonce!=nonce || s->sequence!=seq)return r;
 /* Consume before any callback, including failure. No retry/rearm API. */
 s->consumed=1;r.accepted=1;
 r.result=aib_strict_hold(io,mask,budget,timeout);return r;
}
