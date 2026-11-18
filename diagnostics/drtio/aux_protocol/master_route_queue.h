/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_route_setup.h"
#include "master_ack_slot.h"
/* Host-only composition. pending must nondestructively report0 empty,1 queued,
 * other error under exclusive ownership. Empty is a snapshot, NOT proof against
 * a delayed duplicate arriving afterward. No packet draining/discard/retry here.
 */
struct mq_transport {struct ma_slot_state slot;struct ma_slot_io rx;void *ctx;
 int (*pending)(void *);int (*send)(void *,const uint8_t *,size_t);unsigned failed;};
static inline int mq_send_checked(void *ctx,const uint8_t *bytes,size_t n) {
 struct mq_transport *q=ctx;
 if(q->failed||q->slot.poisoned)return -1;
 if(q->pending(q->ctx)!=0){q->failed=1;return -1;}
 if(q->send(q->ctx,bytes,n)){q->failed=1;return -1;}
 return 0;
}
static inline int mq_recv_slot(void *ctx,uint32_t *kind) {
 struct mq_transport *q=ctx;
 if(q->failed)return -1;
 int result=ma_receive(&q->slot,&q->rx,kind);
 if(result<0)q->failed=1;
 return result;
}
static inline int mq_route_once(struct mr_setup *s,struct mq_transport *q,uint32_t budget) {
 if(!q||!q->pending||!q->send||!q->rx.acquire||!q->rx.release)return MT_INVALID;
 struct mr_io io={q,mq_send_checked,mq_recv_slot};
 return mr_run_once(s,&io,budget);
}
