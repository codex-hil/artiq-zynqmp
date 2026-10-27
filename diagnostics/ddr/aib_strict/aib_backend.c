/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "aib_backend.h"
#define REQ UINT32_C(0xff413030)
#define TYPE UINT32_C(0xff413038)
#define ACK UINT32_C(0xff413040)
static int read_reg(void *ctx,enum aib_reg reg,uint32_t *out) {
 struct aib_backend *b=ctx;uint32_t address;
 if(!b || !b->ready || !out)return -1;
 switch(reg) {case AIB_REQ:address=REQ;break;case AIB_TYPE:address=TYPE;break;
 case AIB_ACK:address=ACK;break;default:return -1;}
 return b->transport.read32(b->transport.ctx,address,out);
}
static int write_request(void *ctx,uint32_t value) {
 struct aib_backend *b=ctx;uint32_t req,type;
 if(!b || !b->ready || b->write_attempted)return -1;
 b->write_attempted=1;
 if(value!=(b->initial_request|b->mask))return -1;
 if(b->transport.read32(b->transport.ctx,REQ,&req) ||
    b->transport.read32(b->transport.ctx,TYPE,&type))return -1;
 if(req!=b->initial_request || type!=b->initial_type)return -1;
 /* Preserve every unrelated bit. This is not an atomic compare-and-swap. */
 return b->transport.write32(b->transport.ctx,REQ,value);
}
static int ticks(void *ctx,uint64_t *value) {
 struct aib_backend *b=ctx;
 if(!b || !b->ready || !value)return -1;
 return b->transport.ticks(b->transport.ctx,value);
}
int aib_backend_prepare(struct aib_backend *b,const struct aib_transport *t,uint32_t mask) {
 uint32_t req,after,ack,type;
 if(!b || b->sealed || !t || !t->read32 || !t->write32 || !t->ticks ||
    !mask || (mask&~UINT32_C(0x30000)))return -1;
 b->sealed=1;b->ready=0;b->write_attempted=0;b->mask=mask;b->transport=*t;
 if(t->read32(t->ctx,REQ,&req) || t->read32(t->ctx,TYPE,&type) ||
    t->read32(t->ctx,ACK,&ack) || t->read32(t->ctx,REQ,&after))return -1;
 if(req!=after || ((req|ack)&mask))return -1;
 b->initial_request=req;b->initial_type=type;
 b->io.ctx=b;b->io.read=read_reg;b->io.write_request=write_request;b->io.ticks=ticks;
 b->ready=1;return 0;
}
