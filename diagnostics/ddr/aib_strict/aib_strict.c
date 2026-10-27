/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "aib_strict.h"
static int snapshot(const struct aib_io *io,uint32_t *req,uint32_t *ack,uint32_t *type) {
 uint32_t after;
 if(io->read(io->ctx,AIB_REQ,req) || io->read(io->ctx,AIB_TYPE,type) ||
    io->read(io->ctx,AIB_ACK,ack) || io->read(io->ctx,AIB_REQ,&after))return -1;
 return *req==after ? 0 : 1;
}
struct aib_result aib_strict_hold(const struct aib_io *io,uint32_t mask,
 uint32_t budget,uint64_t timeout) {
 struct aib_result r={0};uint32_t req,ack,type;uint64_t start,now,last;int rc;
 r.status=AIB_REJECTED;r.mask=mask;
 if(!io || !io->read || !io->write_request || !io->ticks || !mask ||
    (mask & ~UINT32_C(0x30000)) || !budget || budget>1024 || !timeout)return r;
 if(io->ticks(io->ctx,&start)){r.status=AIB_IO_UNCERTAIN;return r;}
 last=start;rc=snapshot(io,&req,&ack,&type);
 if(rc){r.status=rc<0 ? AIB_IO_UNCERTAIN : AIB_CHANGED;return r;}
 r.original_request=req;r.response_type=type;r.last_ack=ack;
 if((req|ack)&mask)return r;
 /* Recheck time before the only request write. No atomic reservation implied. */
 if(io->ticks(io->ctx,&now)){r.status=AIB_IO_UNCERTAIN;return r;}
 if(now<last){r.status=AIB_CLOCK_ERROR;return r;}
 if(now-start>=timeout){r.status=AIB_TIMEOUT;return r;}
 last=now;r.requested_word=req|mask;r.write_attempted=1;
 if(io->write_request(io->ctx,r.requested_word)){r.status=AIB_IO_UNCERTAIN;return r;}
 for(uint32_t i=0;i<budget;i++) {
  if(io->ticks(io->ctx,&now)){r.status=AIB_IO_UNCERTAIN;return r;}
  if(now<last){r.status=AIB_CLOCK_ERROR;return r;}
  if(now-start>=timeout){r.status=AIB_TIMEOUT;return r;}last=now;
  rc=snapshot(io,&req,&ack,&type);r.polls++;
  if(rc){r.status=rc<0 ? AIB_IO_UNCERTAIN : AIB_CHANGED;return r;}
  r.last_ack=ack;
  if(req!=r.requested_word || type!=r.response_type){r.status=AIB_CHANGED;return r;}
  if(io->ticks(io->ctx,&now)){r.status=AIB_IO_UNCERTAIN;return r;}
  if(now<last){r.status=AIB_CLOCK_ERROR;return r;}
  if(now-start>=timeout){r.status=AIB_TIMEOUT;return r;}last=now;
  if((ack&mask)==mask){r.status=AIB_DRAIN_OBSERVED;return r;}
 }
 r.status=AIB_TIMEOUT;return r;
}
